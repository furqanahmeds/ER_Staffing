# LinkedIn Post Draft — ER Staffing Simulation

*Attach: `before_after_chart.png`. Fill in [your repo link] before posting.*

---

## Option A — short version

I spent two weeks this summer building a simulation of an ER's patient flow, using synthetic patient data and real national hospital benchmarks.

The starting point: with typical staffing, my model showed patients could end up waiting over 20 hours during busy periods — the kind of thing that happens when a system doesn't have enough capacity to keep up with demand and just slowly falls further behind.

I then tested dozens of staffing combinations to find one that actually worked. The result: a modest staffing change (roughly one-third more capacity, reallocated smartly across nurses, treatment bays, and physicians rather than just adding people everywhere) cut typical wait times from over 20 hours to under 2 minutes.

This was my first project applying a systems engineering approach end to end — define requirements, build a model, validate it against real data, find the bottleneck, and test solutions against a cost trade-off, not just "make it faster." Exactly the kind of thinking I'm hoping to apply in an internship this year.

Full write-up and code: [your repo link]

#SystemsEngineering #IndustrialEngineering #TAMU #ISEN

---

## Option B — slightly longer, more narrative

Two weeks, one simulation, and a lesson in why "just add more staff" isn't always the right answer.

This summer I built a discrete-event simulation of an emergency room, using synthetic patient records and real national ER benchmarks (NHAMCS) to keep it grounded in reality. The goal: understand how patient wait times respond to staffing levels, and find a staffing plan that actually meets a reasonable service target.

The baseline result was rough — under normal patient volume, my model showed typical wait times exceeding 20 hours during peak periods. Digging into why, I found the bottleneck wasn't staff in general, it was specifically treatment bay availability — running at over 90% capacity, which is the point where wait times start climbing out of control.

From there I tested nearly 100 different staffing combinations — different numbers of nurses, treatment bays, and physicians — scored against both wait-time targets and staffing cost. The winning configuration needed about a third more staffing investment than the baseline, but reduced typical wait times from 20+ hours down to under 2 minutes, while actually needing fewer physicians than some of the worse-performing combinations. Turns out where you put the resources matters more than how many you throw at the problem.

This was my first project running the full systems engineering process — requirements, modeling, validation against real data, root-cause analysis, and a documented cost/performance trade study — rather than just building something that "works." It's exactly the kind of problem-solving I want to bring into an internship.

Code, data sources, and full methodology write-up here: [your repo link]

#SystemsEngineering #IndustrialEngineering #OperationsResearch #TAMU #ISEN

---

## Notes for posting
- LinkedIn algorithm favors posts where you don't link out in the *first* line — consider putting the repo link in a comment instead of the post body, then referencing "link in comments" in the post text.
- Post the `before_after_chart.png` image directly (not the multi-series trade-space plot) — it's the one built for a general audience.
- Good time to tag TAMU ISEN or relevant student orgs if you want more reach within your target audience (recruiters who follow the department page, etc.)
