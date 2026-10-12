# Learner model
LearnSphere uses Bayesian Knowledge Tracing with prior `.25`, learn `.12`, slip `.10`, guess `.20`. Given response correctness `c`, posterior is `P(L|c)=P(c|L)P(L)/(P(c|L)P(L)+P(c|~L)(1-P(L)))`; after the item, `P(L)'=posterior+(1-posterior)*learn`. State, attempts, and timestamp persist in SQLite. This is a transparent model assumption, not evidence of real learning gain.
