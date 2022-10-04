# Quick and Dirty Planner Call

While this package focusses only on the PDDL compilation, and you are strongly encouraged to find your own planner to experiment with, we have included
calls to two popular classical planning engines to help you get started quickly. You can find them [here](planners.py).

| Name      | Type                         | Learn more |
|:----------|:-----------------------------|:-----------|
| Michael   | Optimal, Top-K/Quality, Cost | [[link](https://hub.docker.com/r/ctpelok77/ibmresearchaiplanningsolver)] |
| Christian | Agile, 10 second timeout     | [[link](https://solver.planning.domains/)] |

Note that the integration tests are written for an optimal planner, and so Christian may not pass all tests. 
