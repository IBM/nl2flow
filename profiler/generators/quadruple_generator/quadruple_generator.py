from typing import List, Optional
from profiler.data_types.quadruple_generator_data_types import (
    Quadruple,
)
from profiler.test_helpers.profiler_test_helper import read_remove_pddl_plan
from profiler.generators.quadruple_generator.quadruple_generator_helper import (
    run_pytest,
    separate_docstring,
    get_function_code,
    get_files_in_folder,
    get_class_method_names,
    get_names_with_prefix,
    is_test_file_name,
    get_setup_code_doctring_lists,
)
from profiler.generators.quadruple_generator.quadruple_generator_variables import (
    TEST_PREFIX,
    SETUP_PREFIX,
)


def get_quadruple(
    test_file_path: str,
    test_name: str,
    setup_code_str: str = "",
    setup_doc_str: str = "",
    method_names: List[str] = [],
) -> Optional[Quadruple]:
    """
    test_file_path: the file path for a test
    (i.e. "./tests/profiler/generators/quadruple_generator/test_quadruple_generator.py")
    test_name: the name of a test (i.e. "test_basic_test_output")
    """
    run_pytest(test_file_path, test_name)
    code_str, docstring_str = separate_docstring(get_function_code(test_file_path, test_name, method_names))
    code_str = setup_code_str + code_str

    if len(docstring_str) == 0:
        return None
    docstring_str = setup_doc_str + docstring_str
    valid_pddl_plan_data = True
    try:
        domain_pddl_str, problem_pddl_str, plan_str = read_remove_pddl_plan(test_file_path)
    except Exception as e:
        print(e)
        valid_pddl_plan_data = False

    return (
        Quadruple(
            code=code_str,
            description=docstring_str,
            pddl_doamin=domain_pddl_str,
            pddl_problem=problem_pddl_str,
            plan=plan_str,
        )
        if valid_pddl_plan_data
        else None
    )


def get_quadruples_from_test_file(
    test_method_names: List[str],
    file_path: str,
    setup_code_list: List[str],
    setup_doc_str_list: List[str],
    method_names: List[str],
) -> List[Quadruple]:
    quadruples: List[Quadruple] = list()
    for test_method_name in test_method_names:
        quadruple = get_quadruple(
            file_path,
            test_method_name,
            "\n".join(setup_code_list),
            "\n".join(setup_doc_str_list),
            method_names,
        )
        if quadruple is not None:
            quadruples.append(quadruple)

    return quadruples


def get_quadruples_from_folder(folder_path: str) -> List[Quadruple]:
    quadruples: List[Quadruple] = list()
    file_paths, folder_paths = get_files_in_folder(folder_path)
    for folder_path in folder_paths:
        quadruples.extend(get_quadruples_from_folder(folder_path))
    for file_path in file_paths:
        file_name = file_path.split("/")[-1]
        if not is_test_file_name(file_name):
            continue  # only handle test files
        method_names = get_class_method_names(file_path)
        # setup methods
        setup_code_list, setup_doc_str_list = get_setup_code_doctring_lists(
            get_names_with_prefix(method_names, SETUP_PREFIX), file_path, method_names
        )
        # test methods
        quadruples.extend(
            get_quadruples_from_test_file(
                get_names_with_prefix(method_names, TEST_PREFIX),
                file_path,
                setup_code_list,
                setup_doc_str_list,
                method_names,
            )
        )

    return quadruples
