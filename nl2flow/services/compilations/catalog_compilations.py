from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.schemas import SignatureItem, Parameter
from nl2flow.compile.options import TypeOptions
from nl2flow.services.schemas.sketch_schemas import Catalog, Signature


def basic_catalog_compilation(flow: Flow, catalog: Catalog) -> None:
    for agent in catalog.agents:
        new_agent = Operator(agent.id)

        for index, signature_items in enumerate([agent.inputs, agent.outputs]):
            new_signature_item = SignatureItem(
                parameters=[
                    Parameter(item_id=item.name, item_type=item.type or TypeOptions.ROOT.value)
                    for item in signature_items
                    if isinstance(item, Signature)
                ]
            )

            if not index:
                new_agent.add_input(new_signature_item)

            else:
                new_agent.add_output(new_signature_item)

        flow.add(new_agent)
