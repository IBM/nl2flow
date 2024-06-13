from nl2flow.compile.options import BasicOperations

ask_description = (
    f"The system has action {BasicOperations.SLOT_FILLER.value}."
    + f" Action {BasicOperations.SLOT_FILLER.value} lets the system ask the user about the value of "
    + "any variable unless that variable is explicitly marked as cannot be "
    + f"acquired from the user. Action {BasicOperations.SLOT_FILLER.value} is less preferred "
    + "than acquiring the value of a variable through other actions."
)
map_description = (
    f"Action {BasicOperations.MAPPER.value} is used when a value for one variable can be used for another variable."
)
action_requirement = "To execute an action the values of their inputs must be known."
system_goal_description = "The goal of the system is to execute one or more actions."
