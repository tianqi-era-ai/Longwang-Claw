import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy


class SplitLoop9XML:
    @staticmethod
    def parse_bool(value):
        if isinstance(value, bool):
            return value
        val = str(value).strip().lower()
        if val in ("true", "1", "yes", "y", "on"):
            return True
        if val in ("false", "0", "no", "n", "off"):
            return False
        raise argparse.ArgumentTypeError("Expected a boolean value (true/false).")

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(
            description="Split Loop9 OpenCode master XML into generated markdown files."
        )
        parser.add_argument(
            "--master",
            default=None,
            help="Path to master XML file. Defaults to .opencode/xml/loop9.master.xml relative to this script.",
        )
        parser.add_argument(
            "--outdir",
            default=None,
            help="Output directory for generated files. Defaults to .opencode relative to this script.",
        )
        parser.add_argument(
            "--strict",
            nargs="?",
            const=True,
            default=True,
            type=SplitLoop9XML.parse_bool,
            help="Strict mode (default: true). Use --strict=false to disable.",
        )
        return parser.parse_args()

    @staticmethod
    def default_paths():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # .opencode
        default_master = os.path.join(base_dir, "_xml", "loop9.master.xml")
        default_outdir = base_dir
        return default_master, default_outdir

    @staticmethod
    def ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def build_defs_map(root):
        defs = root.find("defs")
        ref_map = {}
        dup_ids = []
        if defs is None:
            return ref_map, dup_ids

        def collect(node):
            ref_id = node.attrib.get("id")
            if ref_id:
                if ref_id in ref_map:
                    dup_ids.append(ref_id)
                ref_map[ref_id] = node
            for c in list(node):
                collect(c)

        collect(defs)
        return ref_map, dup_ids

    @staticmethod
    def inline_includes(node, ref_map, missing_refs):
        # Recursively inline <include ref="..."/>
        for child in list(node):
            if child.tag == "include":
                ref_id = child.attrib.get("ref")
                insert_at = list(node).index(child)
                if not ref_id or ref_id not in ref_map:
                    missing_refs.append(ref_id or "<missing>")
                    placeholder = ET.Comment(f"Missing include ref: {ref_id}")
                    node.insert(insert_at, placeholder)
                    node.remove(child)
                    continue
                referenced = ref_map[ref_id]
                ref_children = list(referenced)
                if ref_children:
                    for ref_child in ref_children:
                        ref_copy = deepcopy(ref_child)
                        node.insert(insert_at, ref_copy)
                        SplitLoop9XML.inline_includes(ref_copy, ref_map, missing_refs)
                        insert_at += 1
                else:
                    ref_copy = deepcopy(referenced)
                    node.insert(insert_at, ref_copy)
                    SplitLoop9XML.inline_includes(ref_copy, ref_map, missing_refs)
                node.remove(child)
            else:
                SplitLoop9XML.inline_includes(child, ref_map, missing_refs)

    @staticmethod
    def element_to_pretty_xml(elem):
        # Minimal pretty printer; no external deps
        def indent(e, level=0):
            i = "\n" + level * "\t"
            if len(e):
                if not e.text or not e.text.strip():
                    e.text = i + "\t"
                for c in list(e):
                    indent(c, level + 1)
                if not e.tail or not e.tail.strip():
                    e.tail = i
            else:
                if level and (not e.tail or not e.tail.strip()):
                    e.tail = i

        ecopy = deepcopy(elem)
        indent(ecopy)
        return ET.tostring(ecopy, encoding="unicode")

    @staticmethod
    def yaml_quote_string(value: str) -> str:
        # Use JSON string form; valid YAML scalar.
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def yaml_dump(obj, indent=0, key_order=None):
        sp = "  " * indent

        def dump_scalar(v):
            if isinstance(v, bool):
                return "true" if v else "false"
            if isinstance(v, (int, float)):
                return str(v)
            if v is None:
                return "null"
            return SplitLoop9XML.yaml_quote_string(str(v))

        if isinstance(obj, dict):
            lines = []
            keys = list(obj.keys())
            if key_order:
                ordered = [k for k in key_order if k in obj]
                rest = [k for k in keys if k not in set(ordered)]
                keys = ordered + rest
            for k in keys:
                v = obj[k]
                # Quote keys that would be parsed as special tokens.
                key_str = k
                if k == "*" or any(ch in k for ch in [":", "#", "\"", "'", " "]):
                    key_str = SplitLoop9XML.yaml_quote_string(k)
                if isinstance(v, (dict, list)):
                    lines.append(f"{sp}{key_str}:")
                    lines.extend(SplitLoop9XML.yaml_dump(v, indent=indent + 1))
                else:
                    lines.append(f"{sp}{key_str}: {dump_scalar(v)}")
            return lines
        if isinstance(obj, list):
            lines = []
            for item in obj:
                if isinstance(item, (dict, list)):
                    lines.append(f"{sp}-")
                    lines.extend(SplitLoop9XML.yaml_dump(item, indent=indent + 1))
                else:
                    lines.append(f"{sp}- {dump_scalar(item)}")
            return lines

        # Scalar
        return [f"{sp}{dump_scalar(obj)}"]

    @staticmethod
    def extract_frontmatter(frontmatter_elem):
        # Converts <frontmatter> subtree into nested python dict.
        if frontmatter_elem is None:
            return {}

        def text_of(node):
            if node is None:
                return ""
            return (node.text or "").strip()

        fm = {}
        for child in list(frontmatter_elem):
            tag = child.tag
            if tag == "tools":
                tools = {}
                for t in list(child):
                    tools[t.tag] = SplitLoop9XML.parse_bool(text_of(t))
                fm["tools"] = tools
                continue
            if tag == "permission":
                perm = {}
                for section in list(child):
                    section_map = {}
                    entries = list(section.findall("entry"))
                    # stable order: "*" first, then lexicographic
                    def entry_sort_key(e):
                        k = e.attrib.get("key", "")
                        return (0 if k == "*" else 1, k)

                    for e in sorted(entries, key=entry_sort_key):
                        k = e.attrib.get("key")
                        if k is None:
                            continue
                        section_map[k] = text_of(e)
                    perm[section.tag] = section_map
                fm["permission"] = perm
                continue

            value_text = text_of(child)
            if tag in ("temperature", "top_p"):
                try:
                    fm[tag] = float(value_text)
                except ValueError:
                    fm[tag] = value_text
                continue
            if tag in ("steps",):
                try:
                    fm[tag] = int(value_text)
                except ValueError:
                    fm[tag] = value_text
                continue
            if tag in ("subtask", "disable", "hidden"):
                fm[tag] = SplitLoop9XML.parse_bool(value_text)
                continue

            fm[tag] = value_text

        return fm

    @staticmethod
    def wrap_markdown(frontmatter_dict, body_text, key_order=None):
        lines = ["---"]
        yaml_lines = SplitLoop9XML.yaml_dump(frontmatter_dict, indent=0, key_order=key_order)
        lines.extend(yaml_lines)
        lines.append("---")
        lines.append("")
        content = "\n".join(lines) + "\n" + body_text.rstrip() + "\n"
        return content

    @staticmethod
    def validate_forbidden_sequences(text: str):
        # Avoid OpenCode prompt expansions and shell embedding triggers.
        if "@" in text:
            raise ValueError("Forbidden character '@' found in generated content.")
        if "!`" in text:
            raise ValueError("Forbidden sequence '!`' found in generated content.")

    @staticmethod
    def generate(master: str, outdir: str, strict: bool = True) -> None:
        if not os.path.exists(master):
            raise FileNotFoundError(f"Master XML not found: {master}")

        tree = ET.parse(master)
        root = tree.getroot()

        ref_map, dup_ids = SplitLoop9XML.build_defs_map(root)
        if dup_ids:
            msg = f"Duplicate def ids: {', '.join(sorted(set(dup_ids)))}"
            if strict:
                raise ValueError(msg)
            print(f"[WARN] {msg}")

        opencode = root.find("opencode")
        if opencode is None:
            raise ValueError("Missing <opencode> section in master XML")

        # Iterate outputs in document order for stability.
        for unit in list(opencode):
            if unit.tag not in ("command", "agent"):
                continue
            outfile = unit.attrib.get("outfile")
            unit_id = unit.attrib.get("id")
            if not outfile:
                msg = f"Missing outfile for {unit.tag} id={unit_id}"
                if strict:
                    raise ValueError(msg)
                print(f"[WARN] {msg}")
                continue

            frontmatter_elem = unit.find("frontmatter")
            fm = SplitLoop9XML.extract_frontmatter(frontmatter_elem)

            # Body
            if unit.tag == "command":
                template_elem = unit.find("template")
                template_text = (template_elem.text or "").strip("\n") if template_elem is not None else ""
                body = template_text.strip() + "\n"
                key_order = ["description", "agent", "model", "subtask"]
            else:
                prompt_elem = unit.find("prompt")
                if prompt_elem is None or len(list(prompt_elem)) == 0:
                    msg = f"Missing <prompt> content for agent id={unit_id}"
                    if strict:
                        raise ValueError(msg)
                    print(f"[WARN] {msg}")
                    body = ""
                else:
                    prompt_root = list(prompt_elem)[0]
                    prompt_copy = deepcopy(prompt_root)
                    missing_refs = []
                    SplitLoop9XML.inline_includes(prompt_copy, ref_map, missing_refs)
                    if missing_refs:
                        missing_list = ", ".join(sorted(set(missing_refs)))
                        msg = f"Missing include refs in agent {unit_id}: {missing_list}"
                        if strict:
                            raise ValueError(msg)
                        print(f"[WARN] {msg}")
                    body = SplitLoop9XML.element_to_pretty_xml(prompt_copy)
                key_order = ["description", "mode", "model", "variant", "temperature", "top_p", "steps", "tools", "permission", "disable", "hidden", "color", "options"]

            md = SplitLoop9XML.wrap_markdown(fm, body_text=body, key_order=key_order)

            # Validate forbidden sequences in the final markdown content.
            SplitLoop9XML.validate_forbidden_sequences(md)

            target_path = os.path.join(outdir, outfile)
            SplitLoop9XML.ensure_dir(os.path.dirname(target_path))
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[OK] Wrote {target_path}")


def main() -> int:
    args = SplitLoop9XML.parse_args()
    default_master, default_outdir = SplitLoop9XML.default_paths()
    master = args.master or default_master
    outdir = args.outdir or default_outdir
    SplitLoop9XML.generate(master=master, outdir=outdir, strict=args.strict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
