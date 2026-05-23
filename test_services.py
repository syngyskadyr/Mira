from data.tasks import seed_tasks
from backend.services import (
    register_user,
    get_next_task,
    submit_proof,
    get_leaderboard,
    get_user_profile,
    get_referral_link,
)


def main():
    seed_tasks()
    u = register_user(telegram_id=12345, username="alice", segment="student")
    print("registered:", u)
    task = get_next_task(u["user_id"]) if u else None
    print("next task:", task)
    if task:
        proof = "x" * 60 if task["proof_type"] == "text" else "screenshot_data"
        res = submit_proof(u["user_id"], task["task_id"], task["proof_type"], proof)
        print("submission:", res)

    print("leaderboard:", get_leaderboard())
    print("profile:", get_user_profile(12345))
    print("referral link:", get_referral_link(12345))


if __name__ == "__main__":
    main()
