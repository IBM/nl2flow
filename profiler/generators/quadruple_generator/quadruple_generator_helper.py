import ast
import os
import re
import subprocess
from typing import List, Tuple
from profiler.generators.quadruple_generator.quadruple_generator_variables import (
    TEST_PREFIX,
    BASE_TEST_INVOCATION,
    BASE_TEST_FILE_PATH,
    SETUP_METHOD_SIGNATURE,
    FLOW_DEFINITION,
)


def get_idx_list_str(lines: List[str], str_to_match: str) -> int:
    for idx, line in enumerate(lines):
        if str_to_match in line:
            return idx

    return len(lines)


def get_indent_size(input: str) -> int:
    cnt = 0
    for c in input:
        if c == " ":
            cnt += 1
        else:
            break

    return cnt


def remove_default_indent(inputs: List[str], indent_size: int) -> List[str]:
    output: List[str] = list()
    for input in inputs:
        if len(input) > indent_size:
            output.append(input[indent_size:])
        else:
            output.append(input[:])

    return output


def get_function_code(test_file_path: str, test_name: str, method_names: list[str]) -> str:
    lines: List[str] = list()
    with open(test_file_path, "r") as f:
        lines = f.readlines()
    index_start_function = get_idx_list_str(lines, test_name)
    # end the function before assertions start
    index_end_function = get_idx_list_str(lines[index_start_function:], "assert")
    for method_name in method_names:
        if method_name != test_name:
            tmp_idx = get_idx_list_str(lines[index_start_function:], method_name)
            if tmp_idx < index_end_function:
                # end the function before the next function starts
                index_end_function = tmp_idx - 1

    function_body = lines[index_start_function : index_start_function + index_end_function]

    return "\n".join(function_body)


def get_code_string(original_text: str) -> str:
    ptrn = r'(class|def)(.+)\s+("""[\w\s(),;:-]+""")'
    code_without_doc_string = re.sub(ptrn, r"\1\2", original_text)
    code_lines = code_without_doc_string.split("\n")
    # remove the function signature
    code_lines = code_lines[1:]
    # remove empty lines
    code_lines = list(filter(lambda line: len(line) > 0, code_lines))
    # remove invalid indents
    if len(code_lines) > 0:
        code_lines = remove_default_indent(code_lines, get_indent_size(code_lines[0]))

    return "\n".join(code_lines)


def get_doc_string(original_text: str) -> str:
    ptrn_1 = r'("""[\w\s(),;:-]+""")'
    res = re.findall(ptrn_1, original_text[:])

    return str(res[0].replace('"""', "").strip()) if len(res) > 0 else ""


def separate_docstring(original_text: str) -> Tuple[str, str]:
    """
    returns a fuction body and docstring
    """
    return get_code_string(original_text[:]), get_doc_string(original_text[:])


def run_pytest(test_file_path: str, test_name: str) -> None:
    application_command = ["pytest"]
    file_path = [test_file_path]
    flag_key_word = ["-k"]
    key_words = [test_name]
    flags = ["-rP", "--verbose"]
    tokens: List[str] = application_command + file_path + flag_key_word + key_words + flags
    _ = subprocess.run(tokens, capture_output=False)


def get_method_names_in_classes(classes: List[ast.ClassDef]) -> List[str]:
    method_names: List[str] = list()
    for class_ in classes:
        # print("Class name:", class_.name)
        methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
        for method in methods:
            method_names.append(method.name)

    return method_names


def get_class_method_names(test_file_path: str) -> List[str]:
    with open(test_file_path, "r") as f:
        node = ast.parse(f.read())
    # functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    classes: List[ast.ClassDef] = [n for n in node.body if isinstance(n, ast.ClassDef)]

    return get_method_names_in_classes(classes)


def get_names_with_prefix(names: List[str], prefix: str) -> List[str]:
    """
    returns names with a given prefix
    """
    return list(filter(lambda name: name.startswith(prefix), names))


def get_files_in_folder(folder_path: str) -> Tuple[List[str], List[str]]:
    files = os.listdir(folder_path)
    file_paths = [folder_path + "/" + f for f in files if os.path.isfile(folder_path + "/" + f)]
    folder_paths = [folder_path + "/" + f for f in files if os.path.isdir(folder_path + "/" + f)]

    return file_paths, folder_paths


def is_test_file_name(file_name: str) -> bool:
    return file_name.startswith(TEST_PREFIX) and file_name.endswith(".py")


def does_contain_best_test_invocation(code_str: str) -> bool:
    return BASE_TEST_INVOCATION in code_str


def get_setup_code_doctring_lists(
    setup_method_names: List[str], file_path: str, method_names: List[str]
) -> Tuple[List[str], List[str]]:
    """
    returns setup code and their docstrings
    """
    setup_code_list: List[str] = list()
    setup_doc_str_list: List[str] = list()
    if len(setup_method_names) > 0:
        for setup_method_name in setup_method_names:
            code_str, docstring_str = separate_docstring(get_function_code(file_path, setup_method_name, method_names))
            if does_contain_best_test_invocation(code_str):
                code_str = code_str.replace(BASE_TEST_INVOCATION, "")
                base_test_method_names = get_class_method_names(BASE_TEST_FILE_PATH)
                base_test_method_names.remove("__set_up_default_test_agents")
                setup_code_str, setup_docstring_str = separate_docstring(
                    get_function_code(
                        BASE_TEST_FILE_PATH,
                        SETUP_METHOD_SIGNATURE,
                        base_test_method_names,
                    )
                )
                setup_code_str = setup_code_str.replace("self.flow", "flow")
                if len(setup_code_str) > 0:
                    code_str = FLOW_DEFINITION + "\n" + setup_code_str
                if len(setup_docstring_str) > 0:
                    docstring_str = setup_docstring_str + "/n" + docstring_str
            setup_code_list.append(code_str)
            if len(docstring_str) > 0:
                setup_doc_str_list.append(docstring_str)

    return setup_code_list, setup_doc_str_list
