from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter, Constraint
from nl2flow.compile.options import TypeOptions, ConstraintState
from nl2flow.services.schemas.sketch_schemas import Catalog, Signature


def basic_catalog_compilation(flow: Flow, catalog: Catalog) -> None:
    for agent in catalog.agents:
        new_agent = Operator(agent.id)
        new_agent.max_try = 1

        for index, signature_items in enumerate([agent.inputs, agent.outputs]):
            for item in signature_items:
                if isinstance(item, Signature):
                    new_signature_item = SignatureItem(
                        parameters=Parameter(item_id=item.name, item_type=item.type or TypeOptions.ROOT.value)
                    )

                elif isinstance(item, Constraint):
                    signature_constraint = Constraint(
                        constraint=item.constraint,
                        truth_value=ConstraintState.TRUE.value if index == 1 else None,
                    )

                    new_signature_item = SignatureItem(constraints=[signature_constraint])

                else:
                    raise TypeError("Unknown annotation of catalog entry!")

                if not index:
                    new_agent.add_input(new_signature_item)
                else:
                    new_agent.add_output(new_signature_item)

        flow.add(new_agent)
