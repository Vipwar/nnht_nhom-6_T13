"""
Built-in language presets (Token Specifications via Regular Expressions)
and curated demo source snippets for Topic T13: Automata-based Lexical Analyzer.
"""

from __future__ import annotations

from typing import Dict, List

from .models import TokenSpec


MINILANG_SPECS: List[TokenSpec] = [
    TokenSpec("COMMENT", r"//[^\n]*", 1, True, "comment", "Bình luận một dòng (bỏ qua)"),
    TokenSpec("WHITESPACE", r"[ \t\n\r]+", 2, True, "whitespace", "Khoảng trắng, tab, xuống dòng (bỏ qua)"),
    # Keywords (priority higher than IDENTIFIER so exact keyword wins on conflict)
    TokenSpec("KW_IF", r"if", 3, False, "keyword", "Từ khóa rẽ nhánh if"),
    TokenSpec("KW_ELSE", r"else", 4, False, "keyword", "Từ khóa rẽ nhánh else"),
    TokenSpec("KW_WHILE", r"while", 5, False, "keyword", "Từ khóa vòng lặp while"),
    TokenSpec("KW_FOR", r"for", 6, False, "keyword", "Từ khóa vòng lặp for"),
    TokenSpec("KW_LET", r"let", 7, False, "keyword", "Từ khóa khai báo biến let"),
    TokenSpec("KW_FUNC", r"func", 8, False, "keyword", "Từ khóa khai báo hàm func"),
    TokenSpec("KW_RETURN", r"return", 9, False, "keyword", "Từ khóa trả về return"),
    TokenSpec("KW_PRINT", r"print", 10, False, "keyword", "Từ khóa xuất print"),
    TokenSpec("BOOL_LIT", r"true|false", 11, False, "literal", "Hằng logic true / false"),
    # Literals
    TokenSpec("FLOAT_LIT", r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", 12, False, "literal", "Số thực (hỗ trợ dạng khoa học)"),
    TokenSpec("INT_LIT", r"[0-9]+", 13, False, "literal", "Số nguyên không dấu"),
    TokenSpec("STRING_LIT", r'"([^"\\\n]|\\.)*"', 14, False, "literal", "Chuỗi ký tự (hỗ trợ ký tự escape)"),
    # Identifier
    TokenSpec("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*", 15, False, "identifier", "Định danh biến / tên hàm"),
    # Multi-character operators
    TokenSpec("OP_EQ", r"==", 16, False, "operator", "So sánh bằng"),
    TokenSpec("OP_NEQ", r"!=", 17, False, "operator", "So sánh khác"),
    TokenSpec("OP_LE", r"<=", 18, False, "operator", "Nhỏ hơn hoặc bằng"),
    TokenSpec("OP_GE", r">=", 19, False, "operator", "Lớn hơn hoặc bằng"),
    TokenSpec("OP_AND", r"&&", 20, False, "operator", "Phép hội logic AND"),
    TokenSpec("OP_OR", r"\|\|", 21, False, "operator", "Phép tuyển logic OR"),
    # Single-character operators
    TokenSpec("OP_ASSIGN", r"=", 22, False, "operator", "Phép gán"),
    TokenSpec("OP_LT", r"<", 23, False, "operator", "Nhỏ hơn"),
    TokenSpec("OP_GT", r">", 24, False, "operator", "Lớn hơn"),
    TokenSpec("OP_NOT", r"!", 25, False, "operator", "Phủ định logic NOT"),
    TokenSpec("OP_PLUS", r"\+", 26, False, "operator", "Cộng"),
    TokenSpec("OP_MINUS", r"-", 27, False, "operator", "Trừ"),
    TokenSpec("OP_MUL", r"\*", 28, False, "operator", "Nhân"),
    TokenSpec("OP_DIV", r"/", 29, False, "operator", "Chia"),
    TokenSpec("OP_MOD", r"%", 30, False, "operator", "Chia lấy dư"),
    # Delimiters
    TokenSpec("LPAREN", r"\(", 31, False, "delimiter", "Mở ngoặc tròn"),
    TokenSpec("RPAREN", r"\)", 32, False, "delimiter", "Đóng ngoặc tròn"),
    TokenSpec("LBRACE", r"\{", 33, False, "delimiter", "Mở ngoặc nhọn"),
    TokenSpec("RBRACE", r"\}", 34, False, "delimiter", "Đóng ngoặc nhọn"),
    TokenSpec("LBRACKET", r"\[", 35, False, "delimiter", "Mở ngoặc vuông"),
    TokenSpec("RBRACKET", r"\]", 36, False, "delimiter", "Đóng ngoặc vuông"),
    TokenSpec("SEMICOLON", r";", 37, False, "delimiter", "Chấm phẩy kết thúc lệnh"),
    TokenSpec("COMMA", r",", 38, False, "delimiter", "Dấu phẩy phân tách"),
]


CALCLANG_SPECS: List[TokenSpec] = [
    TokenSpec("WHITESPACE", r"[ \t\n\r]+", 1, True, "whitespace", "Khoảng trắng (bỏ qua)"),
    TokenSpec("KW_LET", r"let", 2, False, "keyword", "Khai báo biến let"),
    TokenSpec("KW_PRINT", r"print", 3, False, "keyword", "In giá trị print"),
    TokenSpec("FLOAT", r"[0-9]+\.[0-9]+", 4, False, "literal", "Số thực thập phân"),
    TokenSpec("INT", r"[0-9]+", 5, False, "literal", "Số nguyên"),
    TokenSpec("ID", r"[a-zA-Z_][a-zA-Z0-9_]*", 6, False, "identifier", "Tên biến"),
    TokenSpec("EQ", r"==", 7, False, "operator", "So sánh bằng =="),
    TokenSpec("ASSIGN", r"=", 8, False, "operator", "Phép gán ="),
    TokenSpec("OP_ARITH", r"\+|-|\*|/", 9, False, "operator", "Toán tử số học + - * /"),
    TokenSpec("LPAREN", r"\(", 10, False, "delimiter", "Ngoặc mở ("),
    TokenSpec("RPAREN", r"\)", 11, False, "delimiter", "Ngoặc đóng )"),
    TokenSpec("SEMI", r";", 12, False, "delimiter", "Chấm phẩy ;"),
]


MINISQL_SPECS: List[TokenSpec] = [
    TokenSpec("COMMENT", r"--[^\n]*", 1, True, "comment", "Bình luận SQL --"),
    TokenSpec("WHITESPACE", r"[ \t\n\r]+", 2, True, "whitespace", "Khoảng trắng"),
    TokenSpec("KW_SELECT", r"SELECT|select", 3, False, "keyword", "Từ khóa SELECT"),
    TokenSpec("KW_FROM", r"FROM|from", 4, False, "keyword", "Từ khóa FROM"),
    TokenSpec("KW_WHERE", r"WHERE|where", 5, False, "keyword", "Từ khóa WHERE"),
    TokenSpec("KW_AND", r"AND|and", 6, False, "keyword", "Từ khóa AND"),
    TokenSpec("KW_OR", r"OR|or", 7, False, "keyword", "Từ khóa OR"),
    TokenSpec("NUMBER", r"[0-9]+(\.[0-9]+)?", 8, False, "literal", "Hằng số nguyên hoặc thực"),
    TokenSpec("STRING", r"'[^'\n]*'", 9, False, "literal", "Chuỗi SQL trong nháy đơn"),
    TokenSpec("IDENT", r"[a-zA-Z_][a-zA-Z0-9_]*", 10, False, "identifier", "Tên bảng / tên cột"),
    TokenSpec("COMP_OP", r"<=|>=|<>|!=|=|<|>", 11, False, "operator", "Toán tử so sánh"),
    TokenSpec("STAR", r"\*", 12, False, "operator", "Ký tự đại diện *"),
    TokenSpec("COMMA", r",", 13, False, "delimiter", "Dấu phẩy"),
    TokenSpec("SEMI", r";", 14, False, "delimiter", "Kết thúc truy vấn ;"),
]


PRESETS: Dict[str, Dict] = {
    "minilang": {
        "id": "minilang",
        "name": "MiniLang (Ngôn ngữ lệnh đầy đủ — 38 token)",
        "description": (
            "Ngôn ngữ lập trình lệnh rút gọn gồm bình luận, từ khóa điều khiển, số nguyên/thực khoa học, "
            "chuỗi có escape, định danh, toán tử 1–2 ký tự và dấu phân cách."
        ),
        "specs": MINILANG_SPECS,
        "samples": {
            "valid": {
                "title": "Chương trình MiniLang hợp lệ",
                "code": (
                    "// Chuong trinh tinh tong va kiem tra dieu kien\n"
                    "func compute(n, rate) {\n"
                    "    let total = 0.0;\n"
                    "    let i = 1;\n"
                    "    while (i <= n && rate >= 1.5e-2) {\n"
                    "        if (i % 2 == 0) {\n"
                    "            total = total + i * rate;\n"
                    "        } else {\n"
                    "            total = total + 1;\n"
                    "        }\n"
                    "        i = i + 1;\n"
                    "    }\n"
                    '    print("Ket qua: \\"OK\\"", total, true);\n'
                    "    return total;\n"
                    "}\n"
                ),
            },
            "edge_cases": {
                "title": "Trường hợp biên (Maximal Munch & Ưu tiên)",
                "code": (
                    "// 1. Maximal Munch: ifx la IDENTIFIER, khong phai KW_IF + x\n"
                    "let ifx = while_2 + return0 + trueValue;\n"
                    "// 2. Toan tu lien ke khong khoang trang: === -> == va =\n"
                    "let flag = a===b && x<=y || z!=0;\n"
                    "// 3. So thuc + quay lui Maximal Munch: 1.5e quay lui 1 ky tu -> FLOAT(1.5) + ID(e)\n"
                    "let pi = 3.14e+2 / 100;\n"
                    "let bt = 1.5e + 2;\n"
                    "// 4. Chuoi rong va chuoi chua dau ngoac kep escape\n"
                    'let empty = "";\n'
                    'let quote = "a \\"b\\" c";\n'
                    "// 5. Binh luan cuoi file khong co ky tu xuong dong"
                ),
            },
            "errors": {
                "title": "Lỗi từ vựng & Phục hồi (Panic-mode Recovery)",
                "code": (
                    "let price = 100$ + @tax;\n"
                    'let broken = "chuoi chua dong;\n'
                    "let badFloat = 3. + 4;\n"
                    "let okAfterError = 42;\n"
                ),
            },
        },
    },
    "calclang": {
        "id": "calclang",
        "name": "CalcLang (Ngôn ngữ biểu thức gọn — 12 token, DFA trực quan)",
        "description": (
            "Bộ ngôn ngữ nhỏ gọn (~16 trạng thái DFA tối giản) lý tưởng để quan sát toàn bộ "
            "đồ thị Combined DFA, bảng chuyển trạng thái và các bước tối thiểu hóa trực tiếp."
        ),
        "specs": CALCLANG_SPECS,
        "samples": {
            "valid": {
                "title": "Biểu thức CalcLang cơ bản",
                "code": (
                    "let x = 3.14;\n"
                    "let letx = (x + 2) * 10;\n"
                    "print(letx == 51.4);\n"
                ),
            },
            "edge_cases": {
                "title": "Maximal Munch & Backtrack",
                "code": "let a=12.5+3.0; print(let_1==a);",
            },
            "errors": {
                "title": "Kiểm tra ký tự lỗi",
                "code": "let x = 5 # 2;\nprint(x);",
            },
        },
    },
    "minisql": {
        "id": "minisql",
        "name": "MiniSQL (Ngôn ngữ truy vấn lệnh — 14 token)",
        "description": (
            "Minh họa khả năng sinh Lexical Analyzer tổng quát cho miền ngôn ngữ khác (SQL) "
            "chỉ bằng cách thay đổi tập Biểu thức chính quy đầu vào."
        ),
        "specs": MINISQL_SPECS,
        "samples": {
            "valid": {
                "title": "Truy vấn SQL hợp lệ",
                "code": (
                    "-- Truy van sinh vien diem cao\n"
                    "SELECT id, name, gpa\n"
                    "FROM students\n"
                    "WHERE gpa >= 3.6 AND major <> 'Unknown' OR id = 101;\n"
                ),
            },
            "edge_cases": {
                "title": "Chuỗi & từ khóa gần giống",
                "code": "select select_id, from_date FROM orders WHERE status != '' AND total <= 99.5;",
            },
            "errors": {
                "title": "Lỗi chuỗi chưa đóng & ký tự lạ",
                "code": "SELECT @col FROM tbl WHERE name = 'unterminated\n;",
            },
        },
    },
}


# Classic single-regex textbook examples (including exact UEH Chap 3.1 slide examples!)
SINGLE_REGEX_EXAMPLES: List[Dict] = [
    {
        "name": "UEH Slide 38: (a|b)*abb",
        "pattern": "(a|b)*abb",
        "note": "Ví dụ kinh điển Thompson NFA 11 trạng thái (0..10) và Subset DFA 5 trạng thái.",
        "sample_inputs": ["abb", "aabb", "babb", "ab", "aba", ""],
    },
    {
        "name": "UEH Slide 46-57: (a|ba)(a|b)*ba",
        "pattern": "(a|ba)(a|b)*ba",
        "note": "Ví dụ trực tiếp trong slide bài giảng Direct RE → DFA (cây phân tích r# và bảng followpos).",
        "sample_inputs": ["aba", "baba", "aabba", "ba", "a", "abb"],
    },
    {
        "name": "Token FLOAT_LIT",
        "pattern": r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?",
        "note": "Biểu thức chính quy nhận dạng số thực và dạng khoa học.",
        "sample_inputs": ["3.14", "0.5e-2", "1.0E+10", "3.", ".5", "42"],
    },
    {
        "name": "Token IDENTIFIER",
        "pattern": r"[a-zA-Z_][a-zA-Z0-9_]*",
        "note": "Biểu thức chính quy nhận dạng định danh biến/hàm.",
        "sample_inputs": ["count", "_tmp1", "ifx", "1abc", "a-b", ""],
    },
    {
        "name": "Token STRING_LIT",
        "pattern": r'"([^"\\\n]|\\.)*"',
        "note": "Nhận dạng chuỗi ký tự có hỗ trợ escape như \\\" và \\n.",
        "sample_inputs": ['"hello"', '""', r'"a\"b"', '"unterminated', 'abc'],
    },
]
