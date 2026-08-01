import asyncio
from backend.database.data_store import data_store
from backend.services.report_aggregation_service import (
    get_overview_kpis,
    get_pipeline_funnel,
)

async def main():
    try:
        await data_store.initialize()
        jobs = await data_store.list_jobs()
        cands = await data_store.list_candidates()
        ivs = await data_store.list_interviews()
        apps = data_store._data.get("applications", []) if data_store._data else []
        emps = await data_store.list_employees()
        print("jobs:", len(jobs))
        print("cands:", len(cands))
        print("ivs:", len(ivs))
        print("emps:", len(emps))
        print("apps:", len(apps))
        print("overview:", get_overview_kpis(jobs, cands, ivs))
        print("funnel:", get_pipeline_funnel(jobs, apps, ivs, cands))
        print("SUCCESS")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("FAILED:", e)

if __name__ == "__main__":
    asyncio.run(main())
