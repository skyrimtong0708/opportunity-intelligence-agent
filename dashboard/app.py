from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opportunity_intel.cli import run_pipeline  # noqa: E402

st.set_page_config(page_title="Opportunity Intelligence", page_icon="🔭", layout="wide")
st.title("Opportunity Intelligence Agent")
st.caption("Evidence → pain points → clusters → scored opportunities → experiments")

snapshot_path = ROOT / "data" / "runtime" / "latest.json"
if st.sidebar.button("Run deterministic pipeline", type="primary"):
    with st.spinner("Running six agent roles across five niches..."):
        run_pipeline()
    st.sidebar.success("Snapshot updated")

if not snapshot_path.exists():
    st.info("No snapshot yet. Run `python -m opportunity_intel.cli run --all` or use the button.")
    st.stop()

snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
niche_id = st.sidebar.selectbox("Niche", list(snapshot), format_func=lambda x: x.replace("_", " ").title())
data = snapshot[niche_id]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Evidence", len(data["evidence"]))
c2.metric("Pain points", len(data["pain_points"]))
c3.metric("Clusters", len(data["clusters"]))
c4.metric("Opportunities", len(data["opportunities"]))

st.subheader("Ranked opportunities")
table = [{"Opportunity": o["title"], "Score": o["score"], "Evidence": len(o["evidence_ids"]), "Offer": o["proposed_offer"]} for o in data["opportunities"]]
st.dataframe(table, use_container_width=True, hide_index=True)

for opp in data["opportunities"]:
    with st.expander(f'{opp["score"]:.2f} · {opp["title"]}'):
        left, right = st.columns(2)
        left.markdown(f'**Problem**  \n{opp["problem"]}')
        left.markdown(f'**Offer**  \n{opp["proposed_offer"]}')
        left.markdown(f'**Customer**  \n{opp["target_customer"]}')
        right.markdown("**Score dimensions**")
        right.bar_chart(opp["dimensions"])
        st.markdown("**Skeptic risks**")
        for risk in opp["risks"]:
            st.write(f"- {risk}")
        st.markdown("**Next experiment**")
        st.json(opp["experiment"])
        evidence_map = {e["id"]: e for e in data["evidence"]}
        st.markdown("**Evidence trail**")
        st.dataframe([evidence_map[eid] for eid in opp["evidence_ids"]], use_container_width=True, hide_index=True)

