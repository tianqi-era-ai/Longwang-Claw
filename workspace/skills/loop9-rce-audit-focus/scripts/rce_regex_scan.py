#!/usr/bin/env python3
"""Language-specific RCE regex scanner.

Current scope:
- implemented: java, php
- extensible later: python, node, dotnet

Design stance:
- keep the verified Java giant-regex asset intact in spirit
- use it as a high-recall helper, not as final vulnerability proof
- reduce noise through language-specific file selection
- persist full scan results to a file for reuse across turns
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import os
from datetime import datetime

WORKSPACE = Path('~/.openclaw/workspace')
JAVA_REGEX_SOURCE_DOC = WORKSPACE / 'Super8/工作流_提示词工程/case31_网络安全_相关Skill/代码审计_RCE相关审计_Skill_设计目录/设计等文档/原始文档/Java的RCE_搜索关键词.md'
PHP_REGEX_SOURCE_DOC = WORKSPACE / 'Super8/工作流_提示词工程/case31_网络安全_相关Skill/代码审计_RCE相关审计_Skill_设计目录/设计等文档/原始文档/PHP的RCE_搜索关键词.md'

# Fallback copy kept inside the Python file as requested.
# Preferred runtime source is the original reviewed document above.
JAVA_RCE_REGEX_JS = r"""/(((public)\s{1,20}(.*)\s{1,20}(readObject))|((\.|\s)readObject\()|((public)\s{1,20}(.*)\s{1,20}(writeObject))|((\.|\s)writeObject\()|((public)\s{1,20}(.*)\s{1,20}(readUnshared))|((\.|\s)readUnshared\()|((public)\s{1,20}(.*)\s{1,20}(readResolve))|((\.|\s)readResolve\()|((public)\s{1,20}(.*)\s{1,20}(writeReplace))|((\.|\s)writeReplace\()|(fastjson)|(jackson)|(gson)|((ac)\s{1,20}(ed)\s{1,20}(00)\s{1,20}(05))|(rO0AB)|((^(?!.*(public)).*(((implements)\s{1,20}(Serializable)))))|((\.|\s)load\()|(yaml(\.|\s)load\()|(\.Yaml;)|((\w*)Yaml(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)Yaml\()|((\.|\s)fromXML\()|(xStream(\.|\s)fromXML\()|(\.XStream;)|((\w*)XStream(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)XStream\()|((\.|\s)readValue\()|(objectMapper(\.|\s)readValue\()|(\.ObjectMapper;)|((\w*)ObjectMapper(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ObjectMapper\()|((\.|\s)parseObject\()|(jSON(\.|\s)parseObject\()|(\.JSON;)|((\w*)JSON(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)JSON\()|((\.|\s)parseObject\()|(jSONObject(\.|\s)parseObject\()|(\.JSONObject;)|((\w*)JSONObject(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)JSONObject\()|((\.|\s)readObject\()|(objectInputStream(\.|\s)readObject\()|((\.|\s)readUnshared\()|(objectInputStream(\.|\s)readUnshared\()|(\.ObjectInputStream;)|((\w*)ObjectInputStream(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ObjectInputStream\()|((\.|\s)readObject\()|(xMLDecoder(\.|\s)readObject\()|(\.XMLDecoder;)|((\w*)XMLDecoder(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)XMLDecoder\()|(resolveClass\()|((\.|\s)accept\()|(validatingObjectInputStream(\.|\s)accept\()|(\.ValidatingObjectInputStream;)|((\w*)ValidatingObjectInputStream(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ValidatingObjectInputStream\()|(()\s{1,20}(transient)\s{1,20}())|(((eval)))|(classLoader)|(__BCEL_MARKER__)|(getSystemClassLoader)|(resolveClass)|(loadClass)|(\.ServiceLoader;)|((\w*)ServiceLoader(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ServiceLoader\()|((\.|\s)getSystemJavaCompiler\()|(toolProvider(\.|\s)getSystemJavaCompiler\()|(\.ToolProvider;)|((\w*)ToolProvider(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ToolProvider\()|(\.JavaFileObject;)|((\w*)JavaFileObject(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)JavaFileObject\()|(\.JdbcRowSetImpl;)|((\w*)JdbcRowSetImpl(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)JdbcRowSetImpl\()|(\.TemplatesImpl;)|((\w*)TemplatesImpl(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)TemplatesImpl\()|(\.TransformerFactoryImpl;)|((\w*)TransformerFactoryImpl(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)TransformerFactoryImpl\()|(javax\.el\.ELProcessor)|((\w*)ELProcessor(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ELProcessor\()|(\.SpelExpressionParser;)|((\w*)SpelExpressionParser(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)SpelExpressionParser\()|(((eval)))|(\.getRuntime\()|(\.start\()|(\.evaluate\()|(exec)|(\.exec\()|(RunTime)|(ProcessBuilder)|(UNIXProcess)|(ProcessImpl)|(getRuntime)|(Runtime\.getRuntime\(\)\.exec\(\))|(quartz)|(定时任务)|(ConCurrent)|((\.|\s)getRuntime\()|(runtime(\.|\s)getRuntime\()|(\.Runtime;)|((\w*)Runtime(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)Runtime\()|(\.Process;)|((\w*)Process(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)Process\()|(\.UNIXProcess;)|((\w*)UNIXProcess(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)UNIXProcess\()|(\.ProcessImpl;)|((\w*)ProcessImpl(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ProcessImpl\()|((\.|\s)start\()|(processBuilder(\.|\s)start\()|(\.ProcessBuilder;)|((\w*)ProcessBuilder(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)ProcessBuilder\()|((\.|\s)evaluate\()|(groovyShell(\.|\s)evaluate\()|(\.GroovyShell;)|((\w*)GroovyShell(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)GroovyShell\()|(\.AbstractQuartzJob;)|((\w*)AbstractQuartzJob(\s+)(\S+)(\s+)=)|(new(\s+)(\w*)AbstractQuartzJob\())/igm"""
PHP_RCE_REGEX_JS = r"""/((eval\s*\()|(assert\s*\()|(create_function\s*\()|(preg_replace\s*\([\s\S]{0,160}?\/e['\"]))|((shell_exec|exec|system|passthru|popen|proc_open|pcntl_exec|expect_popen)\s*\()|(Process::fromShellCommandline)|(Symfony\\Component\\Process\\Process)|(new\s+Process\s*\()|((spl_autoload_register|call_user_func|call_user_func_array)\s*\()|((dl|putenv)\s*\()|((php:\/\/|data:\/\/|zip:\/\/|phar:\/\/|expect:\/\/))|((unserialize|maybe_unserialize|yaml_parse|yaml_parse_file|yaml_parse_url|igbinary_unserialize)\s*\()|((Phar|PharData|PharFileInfo))|((__wakeup|__destruct|__toString|__invoke|__unserialize|__serialize)\s*\()|(Serializable)|(\b__HALT_COMPILER\s*\()|((Twig(_Environment)?|Twig\\Environment|Smarty(BC)?|Blade|Latte|Mustache|Fenom))|((createTemplate|registerPlugin|registerFilter|registerUndefinedFilterCallback|compileString)\s*\()|(__PHP_FILES__)|((move_uploaded_file|is_uploaded_file)\s*\()|((finfo_file|mime_content_type|getimagesize|exif_imagetype|pathinfo)\s*\()|((Imagick|imagecreatefromstring|imagecreatefromjpeg|imagecreatefrompng|imagecreatefromgif|imagecreatefromwebp)\s*\()|(ZipArchive))/igm"""


def normalize_js_regex_literal(literal: str) -> str:
    value = literal.strip()
    if value.startswith('/') and value.endswith('/igm'):
        return value[1:-4]
    raise ValueError('Expected a /.../igm JavaScript-style regex literal')


def load_java_regex_literal() -> str:
    if JAVA_REGEX_SOURCE_DOC.exists():
        text = JAVA_REGEX_SOURCE_DOC.read_text(encoding='utf-8')
        literal = text.strip().removeprefix('```javascript').removesuffix('```').strip()
        return normalize_js_regex_literal(literal)
    dollar = chr(36)
    bcel_marker = dollar + dollar + 'BCEL' + dollar + dollar
    return normalize_js_regex_literal(JAVA_RCE_REGEX_JS.replace('__BCEL_MARKER__', bcel_marker))


def regex_union(patterns: Iterable[str]) -> str:
    return '(?:' + '|'.join(patterns) + ')'


PHP_SUPERGLOBAL_FILES_REGEX = re.escape(chr(36) + '_FILES') + r'\b'

PHP_RCE_PATTERNS = [
    # Direct code / command execution surfaces.
    r'\beval\s*\(',
    r'\bassert\s*\(',
    r'\bcreate_function\s*\(',
    r'\bpreg_replace\s*\([\s\S]{0,160}?/e[\'\"]',
    r'(?<!->)(?<!::)\b(?:shell_exec|exec|system|passthru|popen|proc_open|pcntl_exec|expect_popen)\s*\(',
    r'\b(?:Process::fromShellCommandline|Symfony\\Component\\Process\\Process)\b',
    r'\bnew\s+Process\s*\(',

    # Dynamic loading / execution-adjacent pivots.
    r'\b(?:spl_autoload_register|call_user_func|call_user_func_array)\s*\(',
    r'\b(?:dl|putenv)\s*\(',
    r'\b(?:php://|data://|zip://|phar://|expect://)',

    # Deserialization / object-injection / Phar-related surfaces.
    r'\b(?:unserialize|maybe_unserialize|yaml_parse|yaml_parse_file|yaml_parse_url|igbinary_unserialize)\s*\(',
    r'\b(?:Phar|PharData|PharFileInfo)\b',
    r'\b(?:__wakeup|__destruct|__toString|__unserialize|__serialize)\s*\(',
    r'\bSerializable\b',
    r'\b__HALT_COMPILER\s*\(',

    # Template / render / expression-execution ecosystems.
    r'\b(?:Twig(?:_Environment)?|Twig\\Environment|Smarty(?:BC)?|Blade|Latte|Mustache|Fenom)\b',
    r'\b(?:createTemplate|registerPlugin|registerFilter|registerUndefinedFilterCallback|compileString)\s*\(',

    # Upload / image-processing / archive-progression surfaces relevant to PHP RCE chains.
    PHP_SUPERGLOBAL_FILES_REGEX,
    r'\b(?:move_uploaded_file|is_uploaded_file)\s*\(',
    r'\b(?:finfo_file|mime_content_type|getimagesize|exif_imagetype|pathinfo)\s*\(',
    r'\b(?:Imagick|imagecreatefromstring|imagecreatefromjpeg|imagecreatefrompng|imagecreatefromgif|imagecreatefromwebp)\s*\(',
    r'\b(?:ZipArchive|PharData)\b',
]

PHP_RCE_REGEX = regex_union(PHP_RCE_PATTERNS)


def load_php_regex_literal() -> str:
    if PHP_REGEX_SOURCE_DOC.exists():
        text = PHP_REGEX_SOURCE_DOC.read_text(encoding='utf-8')
        literal = text.strip().removeprefix('```javascript').removesuffix('```').strip()
        if literal.startswith('/') and literal.endswith('/igm'):
            candidate = normalize_js_regex_literal(literal)
            try:
                re.compile(candidate, re.IGNORECASE | re.MULTILINE)
                return candidate
            except re.PatternError:
                pass
    return PHP_RCE_REGEX


@dataclass(frozen=True)
class LanguageRule:
    name: str
    regex_source: str
    suffixes: tuple[str, ...]
    exact_names: tuple[str, ...]
    exclude_dirs: tuple[str, ...]
    description: str

    def compiled(self) -> re.Pattern[str]:
        return re.compile(self.regex_source, re.IGNORECASE | re.MULTILINE)


RULES: dict[str, LanguageRule] = {
    'java': LanguageRule(
        name='java',
        regex_source=load_java_regex_literal(),
        suffixes=(
            '.java', '.jsp', '.jspx', '.tag', '.tagx', '.tld',
            '.xml', '.yml', '.yaml', '.properties',
            '.gradle', '.groovy', '.kt', '.kts',
        ),
        exact_names=(
            'pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle',
            'settings.gradle.kts', 'gradle.properties', 'web.xml', 'beans.xml',
            'application.properties', 'application.yml', 'application.yaml',
        ),
        exclude_dirs=(
            '.git', '.idea', '.vscode', '.gradle', 'node_modules', 'vendor',
            'dist', 'build', 'target', 'out', 'coverage', '__pycache__',
            '.mvn', '.svn', '.hg', 'tmp', 'temp', 'logs',
        ),
        description='Verified giant-regex asset for Java/JVM high-recall RCE scanning.',
    ),
    'php': LanguageRule(
        name='php',
        regex_source=load_php_regex_literal(),
        suffixes=(
            '.php', '.phtml', '.php3', '.php4', '.php5', '.php7', '.php8', '.phps',
            '.inc', '.module', '.install', '.theme', '.tpl', '.twig', '.latte',
            '.ctp', '.phar', '.stub', '.yml', '.yaml', '.ini',
        ),
        exact_names=(
            'composer.json', '.htaccess', 'php.ini',
            'config.php', 'index.php',
        ),
        exclude_dirs=(
            '.git', '.idea', '.vscode', 'node_modules', 'vendor',
            'dist', 'build', 'target', 'out', 'coverage', '__pycache__',
            '.svn', '.hg', 'tmp', 'temp', 'logs', 'cache', 'storage',
        ),
        description='Curated high-recall PHP RCE/progression regex for command execution, deserialization, templates, uploads, and interpreter-adjacent surfaces.',
    ),
}


def iter_candidate_files(root: Path, rule: LanguageRule) -> Iterable[Path]:
    suffixes = set(rule.suffixes)
    exact_names = set(rule.exact_names)
    excluded = set(rule.exclude_dirs)

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excluded]
        current = Path(current_root)
        for filename in filenames:
            path = current / filename
            if filename in exact_names or path.suffix.lower() in suffixes:
                yield path


def line_col_for_index(text: str, index: int) -> tuple[int, int]:
    line = text.count('\n', 0, index) + 1
    last_nl = text.rfind('\n', 0, index)
    col = index + 1 if last_nl == -1 else index - last_nl
    return line, col


def scan_file(path: Path, pattern: re.Pattern[str], max_matches_per_file: int) -> dict | None:
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return {'path': str(path), 'error': str(e)}

    matches = []
    for m in pattern.finditer(text):
        line, col = line_col_for_index(text, m.start())
        # snippet = text[max(0, m.start()-120):min(len(text), m.end()+120)].replace('\n', '\\n')
        matches.append({
            'match': m.group(0)[:200],
            'line': line,
            'col': col,
            # 'snippet': snippet,
        })
        if len(matches) >= max_matches_per_file:
            break

    if not matches:
        return None
    return {'path': str(path), 'matches': matches}


def default_output_path(root: Path, language: str) -> Path:
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    safe_name = root.name or 'repo'
    return root / f'.openclaw-rce-regex-scan-{safe_name}-{language}-{stamp}.json'


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Language-specific RCE regex scanner')
    p.add_argument('root', help='Repository root to scan')
    p.add_argument('--language', required=True, choices=sorted(RULES.keys()))
    p.add_argument('--max-matches-per-file', type=int, default=8)
    p.add_argument('--output-format', choices=['json', 'text'], default='json')
    p.add_argument('--output-path', help='Where to persist the scan result JSON; defaults to a repo-local file')
    return p


def main() -> int:
    args = build_argparser().parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f'Root path is not a directory: {args.root}', file=sys.stderr)
        return 1

    rule = RULES[args.language]
    pattern = rule.compiled()

    candidates = list(iter_candidate_files(root, rule))

    findings = []
    for path in candidates:
        result = scan_file(path, pattern, args.max_matches_per_file)
        if result:
            findings.append(result)

    payload = {
        'language': rule.name,
        'description': rule.description,
        'root': str(root),
        'scanned_file_count': len(candidates),
        'matched_file_count': len(findings),
        'suffixes': list(rule.suffixes),
        'exact_names': list(rule.exact_names),
        'exclude_dirs': list(rule.exclude_dirs),
        'findings': findings,
    }

    output_path = Path(args.output_path).expanduser() if args.output_path else default_output_path(root, rule.name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.output_format == 'json':
        print(json.dumps({
            'language': rule.name,
            'root': str(root),
            'scanned_file_count': len(candidates),
            'matched_file_count': len(findings),
            'output_path': str(output_path),
        }, ensure_ascii=False, indent=2))
    else:
        print(f'language={rule.name}')
        print(f'root={root}')
        print(f'scanned_file_count={len(candidates)}')
        print(f'matched_file_count={len(findings)}')
        print(f'output_path={output_path}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
