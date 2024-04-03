from nl2flow.compile.flow import Flow
from nl2flow.compile.operators import ClassicalOperator as Operator
from nl2flow.compile.options import SlotOptions
from nl2flow.compile.schemas import SignatureItem, SlotProperty, GoalItem, GoalItems
from nl2flow.plan.planners import Kstar, PDDL

PLANNER = Kstar()


class TestISS23:
    # The system has Action a__0, Action a__1, Action a__2, and Action a__3.

    # Variables v__0 and v__2 can be acquired by asking the user.
    # Variables v__1, v__3, and v__4 cannot be acquired by asking the user.

    # The system has Action ask. Action ask is less preferred than acquiring
    # the value of a variable through other actions. Action ask lets the system
    # ask the user about the value of any variable unless that variable is
    # explicitly marked as cannot be acquired from the user.

    # To execute Action a__0, Variable v__2 and Variable v__0 should be known.
    # After executing Action a__0, Variable v__3 and Variable v__4 are known.

    # To execute Action a__3, Variable v__2 and Variable v__0 should be known.
    # After executing Action a__3, Variable v__1 and Variable v__3 are known.

    # To execute Action a__2, Variable v__2 and Variable v__4 should be known.
    # After executing Action a__2, Variable v__1 and Variable v__3 are known.

    # To execute Action a__1, Variable v__2 and Variable v__4 should be known.
    # After executing Action a__1, Variable v__3 and Variable v__1 are known.

    # Action map is used when a value for one variable can be used for another variable.
    # Action map maps variables with the same type.

    # The goal of the system is to execute Action a__2.

    def test_why_no_plan_from_flow(self) -> None:
        flow = Flow(name="ISS32")
        flow.slot_options.add(SlotOptions.last_resort)

        a_0 = Operator(name="a__0")
        a_0.add_input(SignatureItem(parameters=["v__2", "v__0"]))
        a_0.add_output(SignatureItem(parameters=["v__3", "v__4"]))

        a_3 = Operator(name="a__3")
        a_3.add_input(SignatureItem(parameters=["v__2", "v__0"]))
        a_3.add_output(SignatureItem(parameters=["v__1", "v__3"]))

        a_2 = Operator(name="a__2")
        a_2.add_input(SignatureItem(parameters=["v__2", "v__4"]))
        a_2.add_output(SignatureItem(parameters=["v__1", "v__3"]))

        a_1 = Operator(name="a__1")
        a_1.add_input(SignatureItem(parameters=["v__2", "v__4"]))
        a_1.add_output(SignatureItem(parameters=["v__3", "v__1"]))

        flow.add(
            [
                a_0,
                a_1,
                a_2,
                a_3,
                GoalItems(goals=GoalItem(goal_name="a__2")),
                SlotProperty(slot_name="v__1", slot_desirability=0.0),
                SlotProperty(slot_name="v__3", slot_desirability=0.0),
                SlotProperty(slot_name="v__4", slot_desirability=0.0),
            ]
        )

        plans = flow.plan_it(PLANNER)
        print(PLANNER.pretty_print(plans))
        assert len(plans.list_of_plans) > 0

    def test_why_no_plan_from_pddl(self) -> None:
        domain = "(define (domain default_name-domain)\n    (:requirements :equality :typing :action-costs)\n    (:types\n        generic - object\n        operator - object\n        has-done-state - object\n        constraint-status - object\n        datum-state - object\n        num-retries - object\n        object\n    )\n\n    (:constants\n        False True - constraint-status\n        certain uncertain unknown - datum-state\n        new_object_generic_0 v__0 v__1 v__2 v__3 v__4 - generic\n        future past present - has-done-state\n        try_level_0 try_level_1 try_level_2 try_level_3 try_level_4 try_level_5 try_level_6 - num-retries\n        a__0 a__1 a__2 a__3 - operator\n    )\n\n    (:predicates\n        (has_done ?x1 - operator ?x2 - has-done-state)\n        (been_used ?x1 - generic)\n        (new_item ?x1 - generic)\n        (known ?x1 - generic ?x2 - datum-state)\n        (not_slotfillable ?x1 - generic)\n        (is_mappable ?x1 - generic ?x2 - generic)\n        (not_mappable ?x1 - generic ?x2 - generic)\n        (mapped ?x1 - generic)\n        (not_usable ?x1 - generic)\n        (mapped_to ?x1 - generic ?x2 - generic)\n        (connected ?x1 - operator ?x2 - num-retries ?x3 - num-retries)\n        (free ?x1 - generic)\n        (done_goal_pre )\n        (done_goal_post )\n        (has_done_a__0 ?x1 - generic ?x2 - generic ?x3 - num-retries)\n        (has_done_a__3 ?x1 - generic ?x2 - generic ?x3 - num-retries)\n        (has_done_a__2 ?x1 - generic ?x2 - generic ?x3 - num-retries)\n        (has_done_a__1 ?x1 - generic ?x2 - generic ?x3 - num-retries)\n    )\n\n    (:functions\n        (total-cost ) - number\n        (slot_goodness ?x1 - generic) - number\n        (affinity ?x1 - generic ?x2 - generic) - number\n    )\n\n    \n\n    \n    (:action enabler_operator__a__0\n     :parameters (?x0 - generic ?x1 - generic)\n     :precondition (and (not (has_done_a__0 ?x0 ?x1 try_level_0)) (not (has_done_a__0 ?x0 ?x1 try_level_1)))\n     :effect (and\n        (has_done_a__0 ?x0 ?x1 try_level_0)\n        (increase (total-cost ) 5000))\n    )\n\n\n    (:action a__0\n     :parameters (?x0 - generic ?x1 - generic ?pre_level - num-retries ?post_level - num-retries)\n     :precondition (and (mapped_to ?x0 v__2) (known v__2 certain) (mapped_to ?x1 v__0) (known v__0 certain) (has_done_a__0 ?x0 ?x1 ?pre_level) (not (has_done_a__0 ?x0 ?x1 ?post_level)) (connected a__0 ?pre_level ?post_level))\n     :effect (and\n        (has_done a__0 present)\n        (been_used ?x0)\n        (been_used v__2)\n        (been_used ?x1)\n        (been_used v__0)\n        (has_done_a__0 ?x0 ?x1 ?post_level)\n        (free v__3)\n        (known v__3 certain)\n        (free v__4)\n        (known v__4 certain)\n        (not (mapped v__3))\n        (not (mapped v__4))\n        (increase (total-cost ) 1))\n    )\n\n\n    (:action enabler_operator__a__3\n     :parameters (?x0 - generic ?x1 - generic)\n     :precondition (and (not (has_done_a__3 ?x0 ?x1 try_level_0)) (not (has_done_a__3 ?x0 ?x1 try_level_1)))\n     :effect (and\n        (has_done_a__3 ?x0 ?x1 try_level_0)\n        (increase (total-cost ) 5000))\n    )\n\n\n    (:action a__3\n     :parameters (?x0 - generic ?x1 - generic ?pre_level - num-retries ?post_level - num-retries)\n     :precondition (and (mapped_to ?x0 v__2) (known v__2 certain) (mapped_to ?x1 v__0) (known v__0 certain) (has_done_a__3 ?x0 ?x1 ?pre_level) (not (has_done_a__3 ?x0 ?x1 ?post_level)) (connected a__3 ?pre_level ?post_level))\n     :effect (and\n        (has_done a__3 present)\n        (been_used ?x0)\n        (been_used v__2)\n        (been_used ?x1)\n        (been_used v__0)\n        (has_done_a__3 ?x0 ?x1 ?post_level)\n        (free v__1)\n        (known v__1 certain)\n        (free v__3)\n        (known v__3 certain)\n        (not (mapped v__1))\n        (not (mapped v__3))\n        (increase (total-cost ) 1))\n    )\n\n\n    (:action enabler_operator__a__2\n     :parameters (?x0 - generic ?x1 - generic)\n     :precondition (and (not (has_done_a__2 ?x0 ?x1 try_level_0)) (not (has_done_a__2 ?x0 ?x1 try_level_1)))\n     :effect (and\n        (has_done_a__2 ?x0 ?x1 try_level_0)\n        (increase (total-cost ) 5000))\n    )\n\n\n    (:action a__2\n     :parameters (?x0 - generic ?x1 - generic ?pre_level - num-retries ?post_level - num-retries)\n     :precondition (and (mapped_to ?x0 v__2) (known v__2 certain) (mapped_to ?x1 v__4) (known v__4 certain) (has_done_a__2 ?x0 ?x1 ?pre_level) (not (has_done_a__2 ?x0 ?x1 ?post_level)) (connected a__2 ?pre_level ?post_level))\n     :effect (and\n        (has_done a__2 present)\n        (been_used ?x0)\n        (been_used v__2)\n        (been_used ?x1)\n        (been_used v__4)\n        (has_done_a__2 ?x0 ?x1 ?post_level)\n        (free v__1)\n        (known v__1 certain)\n        (free v__3)\n        (known v__3 certain)\n        (not (mapped v__1))\n        (not (mapped v__3))\n        (increase (total-cost ) 1))\n    )\n\n\n    (:action enabler_operator__a__1\n     :parameters (?x0 - generic ?x1 - generic)\n     :precondition (and (not (has_done_a__1 ?x0 ?x1 try_level_0)) (not (has_done_a__1 ?x0 ?x1 try_level_1)))\n     :effect (and\n        (has_done_a__1 ?x0 ?x1 try_level_0)\n        (increase (total-cost ) 5000))\n    )\n\n\n    (:action a__1\n     :parameters (?x0 - generic ?x1 - generic ?pre_level - num-retries ?post_level - num-retries)\n     :precondition (and (mapped_to ?x0 v__2) (known v__2 certain) (mapped_to ?x1 v__4) (known v__4 certain) (has_done_a__1 ?x0 ?x1 ?pre_level) (not (has_done_a__1 ?x0 ?x1 ?post_level)) (connected a__1 ?pre_level ?post_level))\n     :effect (and\n        (has_done a__1 present)\n        (been_used ?x0)\n        (been_used v__2)\n        (been_used ?x1)\n        (been_used v__4)\n        (has_done_a__1 ?x0 ?x1 ?post_level)\n        (free v__3)\n        (known v__3 certain)\n        (free v__1)\n        (known v__1 certain)\n        (not (mapped v__3))\n        (not (mapped v__1))\n        (increase (total-cost ) 1))\n    )\n\n\n    (:action ask\n     :parameters (?x - generic)\n     :precondition (and (not (known ?x certain)) (not (not_slotfillable ?x)))\n     :effect (and\n        (free ?x)\n        (mapped_to ?x ?x)\n        (known ?x certain)\n        (not (not_usable ?x))\n        (not (mapped ?x))\n        (increase (total-cost ) (slot_goodness ?x)))\n    )\n\n\n    (:action map\n     :parameters (?x - generic ?y - generic)\n     :precondition (and (known ?x certain) (is_mappable ?x ?y) (not (not_mappable ?x ?y)) (not (mapped_to ?x ?y)) (not (new_item ?y)) (been_used ?y))\n     :effect (and\n        (known ?y certain)\n        (mapped_to ?x ?y)\n        (mapped ?x)\n        (not (been_used ?y))\n        (not (not_usable ?y))\n        (increase (total-cost ) (affinity ?x ?y)))\n    )\n\n\n    (:action map--free-alt\n     :parameters (?x - generic ?y - generic)\n     :precondition (and (known ?x certain) (is_mappable ?x ?y) (not (not_mappable ?x ?y)) (not (mapped_to ?x ?y)) (not (new_item ?y)) (been_used ?y) (free ?x))\n     :effect (and\n        (known ?y certain)\n        (mapped_to ?x ?y)\n        (mapped ?x)\n        (not (been_used ?y))\n        (not (not_usable ?y))\n        (free ?y)\n        (increase (total-cost ) 1000))\n    )\n\n)"
        problem = "(define (problem default_name-problem)\n    (:domain default_name-domain)\n\n    (:objects\n        \n    )\n\n    (:init\n        (= (slot_goodness v__2) 100000.0)\n        (= (slot_goodness v__0) 100000.0)\n        (= (slot_goodness v__3) 200000.0)\n        (= (slot_goodness v__4) 200000.0)\n        (= (slot_goodness v__1) 200000.0)\n        (= (slot_goodness new_object_generic_0) 150000.0)\n        (= (total-cost ) 0.0)\n        (been_used v__2)\n        (been_used v__0)\n        (been_used v__4)\n        (connected a__1 try_level_0 try_level_1)\n        (connected a__0 try_level_0 try_level_1)\n        (connected a__3 try_level_0 try_level_1)\n        (connected a__2 try_level_0 try_level_1)\n        (new_item new_object_generic_0)\n        (not_slotfillable v__1)\n        (not_slotfillable v__3)\n        (not_slotfillable v__4)\n        (not_mappable new_object_generic_0 v__4)\n        (not_mappable new_object_generic_0 v__1)\n        (not_mappable new_object_generic_0 v__3)\n        (mapped_to v__2 v__2)\n        (mapped_to v__1 v__1)\n        (mapped_to v__3 v__3)\n        (mapped_to v__0 v__0)\n        (mapped_to new_object_generic_0 new_object_generic_0)\n        (mapped_to v__4 v__4)\n    )\n\n    (:goal\n        (has_done a__2 present)\n    )\n\n    \n    \n    (:metric minimize (total-cost ))\n)\n\n"

        raw_planner_response = PLANNER.raw_plan(PDDL(domain=domain, problem=problem))
        assert len(raw_planner_response.list_of_plans) > 0

    #   "sample_hash": "907ea3bd3088a26cee5e610b9ea5bd88",
    #   "agent_info_generator_input": {
    #     "num_agents": 4,
    #     "num_var": 5,
    #     "num_input_parameters": 2,
    #     "num_samples": 30,
    #     "num_goal_agents": 1,
    #     "proportion_coupled_agents": 0.75,
    #     "proportion_slot_fillable_variables": 0.25,
    #     "proportion_mappable_variables": 0.0,
    #     "num_var_types": 0,
    #     "slot_filler_option": null,
    #     "name_generator": "NUMBER",
    #     "error_message": null
    #   },
