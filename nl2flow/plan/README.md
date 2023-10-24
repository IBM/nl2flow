# Quick and Dirty Planner Call

While this package focusses only on the PDDL compilation, and you are strongly encouraged to find your own planner to experiment with, we have included
calls to two popular classical planning engines to help you get started quickly. You can find them [here](planners.py).

| Name      | Type                         | Learn more |
|:----------|:-----------------------------|:-----------|
| Michael   | Optimal, Top-K/Quality, Cost | [[link](https://hub.docker.com/r/ctpelok77/ibmresearchaiplanningsolver)] |
| Christian | Agile, 10 second timeout     | [[link](https://solver.planning.domains/)] |

Note that the integration tests are written for an optimal planner, and so Christian may not pass all tests. 

# The Planner Class

If you want to use your own planner, you can either use the NL2Flow package to generate the desired PDDL compilations and use
it in your application downstream; or you can extend the available planners in the NL2Flow interface with your own planner 
using the [Planner class](planners.py#L110), using the following two methods.

| Method | Description | 
|:-------|:------------|
| plan   | Receives the PDDL files (and other inputs specific to the planner) and produces the raw planner output. |
| parse  | Parses the raw output into a more presentable and / or usable version. | 

The two planners Michael and Christian listed above are both [remote planners](https://github.ibm.com/aicl/nl2flow/blob/main/nl2flow/plan/planners.py#L189), 
which are derived from the parent Planner class. These are accessible through an HTTPS call and thus require an endpoint in their constructors. 
Note that each of these planners have their unique way to invoke them and parse the raw output -- this is also the ask should you bring 
your own into this interface.
