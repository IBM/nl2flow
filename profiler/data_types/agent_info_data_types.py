from __future__ import annotations
from copy import deepcopy
from enum import Enum
import random
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel


class AgentInfoSignatureItem(BaseModel):
    name: str = ""
    data_type: Optional[str] = None
    mappable: Optional[bool] = False
    slot_fillable: Optional[bool] = False


class AgentInfoSignatureType(str, Enum):
    IN_SIG_FULL = "IN_SIG_FULL"
    OUT_SIG_FULL = "OUT_SIG_FULL"


SIGNATURE_TYPES = [AgentInfoSignatureType.IN_SIG_FULL, AgentInfoSignatureType.OUT_SIG_FULL]


class AgentInfoSignature(BaseModel):
    in_sig_full: List[AgentInfoSignatureItem] = []
    out_sig_full: List[AgentInfoSignatureItem] = []

    def get_signature(self, type: AgentInfoSignatureType) -> List[AgentInfoSignatureItem]:
        if type == AgentInfoSignatureType.IN_SIG_FULL:
            return self.in_sig_full
        if type == AgentInfoSignatureType.OUT_SIG_FULL:
            return self.out_sig_full

    def set_signature(
        self, agent_info_signature_items: List[AgentInfoSignatureItem], type: AgentInfoSignatureType
    ) -> None:
        if type == AgentInfoSignatureType.IN_SIG_FULL:
            self.in_sig_full = agent_info_signature_items
        if type == AgentInfoSignatureType.OUT_SIG_FULL:
            self.out_sig_full = agent_info_signature_items


class AgentInfo(BaseModel):
    agent_id: str
    actuator_signature: AgentInfoSignature = AgentInfoSignature()


class PlanAction(BaseModel):
    action_name: str = ""
    parameters: List[str] = []


class Plan(BaseModel):
    plan: List[PlanAction] = []
    metric: float = -1.0


class SimpleActionModel(BaseModel):
    id: str = ""
    input: List[str] = []
    output: List[str] = []


class LLMBasicStat(BaseModel):
    num_correct: int = 0
    num_missing: int = 0
    num_hallucination: int = 0
    total: int = 0

    def set_num_missing(self) -> None:
        self.num_missing = self.total - self.num_correct

    def increment_stat(self, llm_basic_stat: LLMBasicStat) -> None:
        self.total += llm_basic_stat.total
        self.num_correct += llm_basic_stat.num_correct
        self.num_missing += llm_basic_stat.num_missing
        self.num_hallucination += llm_basic_stat.num_hallucination


class JsonTranslationStatModel(BaseModel):
    num_actions: LLMBasicStat = LLMBasicStat()
    num_input_signature_items: LLMBasicStat = LLMBasicStat()
    num_output_signature_items: LLMBasicStat = LLMBasicStat()
    num_mappings: LLMBasicStat = LLMBasicStat()
    num_available_data: LLMBasicStat = LLMBasicStat()
    num_askable_parameters: LLMBasicStat = LLMBasicStat()
    num_unaskable_parameters: LLMBasicStat = LLMBasicStat()
    num_goal_action_ids: LLMBasicStat = LLMBasicStat()


class SimplePlanningModel(BaseModel):
    actions: List[SimpleActionModel] = []
    mappings: Union[List[Tuple[str, str]], List[Tuple[str, str, float]]] = []  # type: ignore
    available_data: Union[List[str], List[Any]] = []  # variable name, variable type
    askable_parameters: List[str] = []
    unaskable_parameters: List[str] = []
    goal_action_ids: List[str] = []

    def get_stat_lists(self, true_list: List[Any], response_list: List[Any]) -> LLMBasicStat:
        true_goal_action_ids = set(map(lambda datum: datum, true_list))
        response_goal_action_ids = set(map(lambda datum: datum, response_list))
        stat = LLMBasicStat(
            num_correct=0,
            num_missing=0,
            num_hallucination=0,
            total=len(true_goal_action_ids),
        )

        for response_mapping in response_goal_action_ids:
            if response_mapping in true_goal_action_ids:
                stat.num_correct += 1
            else:
                stat.num_hallucination += 1

        stat.set_num_missing()

        return stat

    def get_stat_num_actions(self, true_model: SimplePlanningModel) -> LLMBasicStat:
        true_action_ids = list(map(lambda action: action.id, true_model.actions))
        response_action_ids = list(map(lambda action: action.id, self.actions))

        return self.get_stat_lists(true_list=true_action_ids, response_list=response_action_ids)

    def get_stat_num_signature_items(self, true_model: SimplePlanningModel, is_input: bool) -> LLMBasicStat:
        true_action_id_action_dict = {action.id: action for action in true_model.actions}
        stat = LLMBasicStat(num_correct=0, num_missing=0, num_hallucination=0, total=0)

        for action in self.actions:
            if action.id in true_action_id_action_dict:
                true_signature_items = list(
                    true_action_id_action_dict[action.id].input
                    if is_input
                    else true_action_id_action_dict[action.id].output
                )
                response_signature_items = list(action.input if is_input else action.output)

                tmp_stat = self.get_stat_lists(
                    true_list=true_signature_items,
                    response_list=response_signature_items,
                )
                stat.increment_stat(tmp_stat)

        return stat

    def get_stat(self, true_model: SimplePlanningModel) -> JsonTranslationStatModel:
        return JsonTranslationStatModel(
            num_actions=self.get_stat_num_actions(true_model=true_model),
            num_input_signature_items=self.get_stat_num_signature_items(true_model=true_model, is_input=True),
            num_output_signature_items=self.get_stat_num_signature_items(true_model=true_model, is_input=False),
            num_mappings=self.get_stat_lists(true_list=true_model.mappings, response_list=self.mappings),
            num_available_data=self.get_stat_lists(
                true_list=true_model.available_data, response_list=self.available_data
            ),
            num_askable_parameters=self.get_stat_lists(
                true_list=true_model.askable_parameters,
                response_list=self.askable_parameters,
            ),
            num_unaskable_parameters=self.get_stat_lists(
                true_list=true_model.unaskable_parameters,
                response_list=self.unaskable_parameters,
            ),
            num_goal_action_ids=self.get_stat_lists(
                true_list=true_model.goal_action_ids, response_list=self.goal_action_ids
            ),
        )


class AgentInfoUnitModel(BaseModel):
    available_agents: List[AgentInfo]
    goal_agent_ids: List[str]
    mappings: List[Tuple[str, str, float]]
    available_data: List[Tuple[str, Optional[str]]]  # variable name, variable type

    def shuffle_information(self) -> None:
        if len(self.available_agents) > 0:
            random.shuffle(self.available_agents)
        if len(self.mappings) > 0:
            random.shuffle(self.mappings)
        if len(self.available_data) > 0:
            random.shuffle(self.available_data)

    def get_simple_action_models(self) -> List[SimpleActionModel]:
        available_actions: List[SimpleActionModel] = []
        for agent in self.available_agents:
            available_actions.append(
                SimpleActionModel(
                    id=agent.agent_id,
                    input=(
                        list(
                            map(
                                lambda sig_item: sig_item.name,
                                agent.actuator_signature.in_sig_full,
                            )
                        )
                        if agent.actuator_signature.in_sig_full is not None
                        else []
                    ),
                    output=(
                        list(
                            map(
                                lambda sig_item: sig_item.name,
                                agent.actuator_signature.out_sig_full,
                            )
                        )
                        if agent.actuator_signature.out_sig_full is not None
                        else []
                    ),
                )
            )

        return available_actions

    def get_action_variables(self) -> Tuple[List[str], List[str]]:
        """
        returns a tuple of askable and unaskable variable names
        """
        parameter_name_slot_fillable_state_dict: Dict[str, bool] = {}
        for agent in self.available_agents:
            for sig_type in [
                agent.actuator_signature.in_sig_full,
                agent.actuator_signature.out_sig_full,
            ]:
                for sig_item in sig_type:
                    if sig_item.name not in parameter_name_slot_fillable_state_dict:
                        parameter_name_slot_fillable_state_dict[sig_item.name] = False
                    if sig_item.slot_fillable:
                        parameter_name_slot_fillable_state_dict[sig_item.name] = True
        askable_parameters = [name for name, askable in parameter_name_slot_fillable_state_dict.items() if askable]
        unaskable_parameters = [
            name for name, askable in parameter_name_slot_fillable_state_dict.items() if not askable
        ]

        return (askable_parameters, unaskable_parameters)

    def get_simple_planning_model(self) -> SimplePlanningModel:
        askable_parameters, unaskable_parameters = self.get_action_variables()

        return SimplePlanningModel(
            actions=self.get_simple_action_models(),
            mappings=list(map(lambda mapping: (mapping[0], mapping[1]), self.mappings)),
            available_data=list(map(lambda dat: dat[0], self.available_data)),
            askable_parameters=askable_parameters,
            unaskable_parameters=unaskable_parameters,
            goal_action_ids=deepcopy(self.goal_agent_ids),
        )

    def get_simple_planning_model_json_str(self) -> str:
        simple_planning_model = self.get_simple_planning_model()
        return simple_planning_model.model_dump_json()  # type: ignore
