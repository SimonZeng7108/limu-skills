# -*- coding: utf-8 -*-
"""Write one summary file per author-replied thread, grouped into 10 topics."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QA_PATH = ROOT / "data" / "author_qa.json"
OUT_DIR = ROOT / "replies"

CATEGORIES = [
    (
        "01-agent-skills",
        "Agent skills",
        "How people should work with agents: coding, review, depth, and owning a whole project.",
    ),
    (
        "02-agents",
        "Agents",
        "The agent field itself: harness, memory, RSI, consumer agents, and agent vs other bets.",
    ),
    (
        "03-embodied-robotics",
        "Embodied AI and robotics",
        "Robots, VLA, world models, and whether AI can handle the physical world.",
    ),
    (
        "04-research-phd",
        "Research and PhD",
        "Advising, whether to do a PhD, academia vs industry, and how to pick a research topic.",
    ),
    (
        "05-career-hiring",
        "Career and hiring",
        "Jobs, internships, interviews, management tracks, and making a living.",
    ),
    (
        "06-infra-hardware",
        "Infra and hardware",
        "Training infra, chips, compilers, and on-device / edge AI.",
    ),
    (
        "07-learning",
        "Learning AI",
        "How to start, non-CS paths, paper-reading videos, and whether it is too late.",
    ),
    (
        "08-applied-verticals",
        "Applied AI and verticals",
        "Industry apps, startups, recsys, medical, translation, SFT, AI4Science, and voice.",
    ),
    (
        "09-models-safety",
        "Models and safety",
        "Multimodal, finetuning, LLM direction, alignment, and AI safety.",
    ),
    (
        "10-misc",
        "Misc",
        "Jokes, one-liners, housing, liability, and comments that do not fit elsewhere.",
    ),
]

# dialogId -> (category folder, short title, English analysis)
MAP: dict[str, tuple[str, str, str]] = {
    "0001": (
        "01-agent-skills",
        "Programmer skills when code agents land",
        "The asker wants to know what programmers should keep when coding agents write, review, and run code. Li Mu points at tech-lead skills: basic implementation is being eaten, but leading a technical effort is more than that.",
    ),
    "0002": (
        "03-embodied-robotics",
        "Is embodied AI a bubble",
        "Asks whether embodied AI is a bubble and whether it can really land. Li Mu says there is short-term foam, but the direction is natural: after white-collar work comes blue-collar work, and real deployment may take as long as self-driving.",
    ),
    "0003": (
        "04-research-phd",
        "What advisors and students should do now",
        "An advisor-side question: what should mentors still teach, and will students lose to agents. Li Mu says the era of students as cheap labor should end; treat them as independent researchers who finish work with agents, with only high-level guidance from the advisor.",
    ),
    "0004": (
        "07-learning",
        "Will the paper-reading series come back",
        "Fans ask for the old paper-reading videos. Li Mu has not decided the format, because AI has changed what a paper series should even look like.",
    ),
    "0006": (
        "06-infra-hardware",
        "Is on-device AI a real need",
        "Asks if edge / on-device AI is a real demand. Li Mu used to believe in it, was proven wrong by the deep-learning wave, sees some short-term use while GPUs are expensive (for example Mac Mini), and thinks the long-term need stays niche.",
    ),
    "0008": (
        "04-research-phd",
        "Undergrad research that leans on agents",
        "A CS undergrad in an embodied lab feels like a messenger between GPT and Codex, not a real researcher. Li Mu says that is normal while the area is new: after going deep and seeing which agent plans work, understanding follows.",
    ),
    "0010": (
        "01-agent-skills",
        "Agents multiply ability, they do not add it",
        "The asker argues that agents shrink hard-skill gaps and raise the value of problem-finding and decomposition. Li Mu agrees in a sharper form: an agent is a multiplier (x10), not an adder (+10).",
    ),
    "0012": (
        "02-agents",
        "What LLM harnesses will be eaten",
        "Asks which agent harnesses models will swallow and what stays irreplaceable. Li Mu: whatever works in today's harness will likely be absorbed by the next model, then new harness gaps will appear, and people will stop caring about the old layer.",
    ),
    "0014": (
        "04-research-phd",
        "Is a traditional CV PhD outdated",
        "A student who entered research via Li Mu's book asks whether to do a PhD, and whether CV is dead versus LLM or embodied. Li Mu's concern is learning: agents can finish a research loop, so it is unclear what a PhD is for if the human learns less.",
    ),
    "0016": (
        "03-embodied-robotics",
        "Did Astra-style demos kill VLA research",
        "A grad student doing on-device embodied algorithms asks if LLM scale will just solve robotics. Li Mu treats current robot demos as demo-level; quality, latency, and cost still have to prove out.",
    ),
    "0018": (
        "07-learning",
        "When will paper club return",
        "Another request for the old paper-reading sessions. Li Mu says those videos were handmade, and he has not figured out how to make them in an AI world.",
    ),
    "0019": (
        "09-models-safety",
        "Is AI safety a durable field",
        "An NLP grad student is considering AI security / harmful outputs. Li Mu is constructive: safety will keep feeding people because stronger models keep creating new safety problems.",
    ),
    "0022": (
        "05-career-hiring",
        "How will low-skill workers survive",
        "Asks what people without degrees or networks will live on. Li Mu bets on services: robots may get capable, but whether they give the same emotional value is unknown.",
    ),
    "0023": (
        "07-learning",
        "How far non-CS students should go in AI",
        "Non-CS student wants a learning path. Li Mu's advice is short: first use AI to actually do something.",
    ),
    "0024": (
        "07-learning",
        "Where to start vibe coding",
        "Non-AI major wants resources for vibe coding. Same practical answer: make a project with AI.",
    ),
    "0025": (
        "01-agent-skills",
        "Do fundamentals still matter",
        "Asks if low-level knowledge is still worth learning. Li Mu says yes: when he uses an agent on things he does not understand, the result is not good enough.",
    ),
    "0026": (
        "08-applied-verticals",
        "Is medical imaging a real AI need",
        "Asks if medical-image AI is real demand or hype, especially in China. Li Mu thinks imaging is already mature enough to match doctors, and the frontier has moved toward broader diagnosis.",
    ),
    "0027": (
        "02-agents",
        "Agent vs embodied for the next 3-5 years",
        "Asks which has less foam and is more worth committing to. Li Mu will not pick a winner: both look fine; choose by interest and by whether you can join a good team.",
    ),
    "0029": (
        "01-agent-skills",
        "Should a new grad student still learn to code",
        "A first-year grad can finish projects with AI and wonders if coding practice is wasted. Li Mu: you may not write the code, but you still need to review it and understand what the model wrote.",
    ),
    "0030": (
        "05-career-hiring",
        "Infra vs algorithm vs agent jobs",
        "Someone switching fields asks where the openings are, and if they can still become a researcher. Li Mu: agents are more applied so there are more seats; infra and algorithms have fewer companies but a higher bar.",
    ),
    "0031": (
        "05-career-hiring",
        "Degree anxiety and over-using AI at work",
        "A non-elite undergrad intern fears the market's degree filter and feels they learned nothing because of AI. Li Mu: degree matters less later; the real problem is not understanding what the AI is doing behind the work it finishes.",
    ),
    "0032": (
        "05-career-hiring",
        "Are you hiring",
        "Direct ask for a job. Li Mu: the Toronto office is hiring.",
    ),
    "0034": (
        "01-agent-skills",
        "Skills CS PhD students should train",
        "Asks what computer-science PhDs should cultivate now. Li Mu: the ability to get things done, specifically to lead agents through work that used to need a 5-10 person team.",
    ),
    "0035": (
        "03-embodied-robotics",
        "Future of embodied intelligence",
        "Open question on embodied AI's future. Li Mu is mildly positive: if nothing else looks more promising, it is a good direction.",
    ),
    "0036": (
        "07-learning",
        "Is 30 too late to go deep on AI apps",
        "A 30-year-old wants encouragement to build real AI applications. Li Mu: 40 is still in time, so 30 is fine.",
    ),
    "0037": (
        "04-research-phd",
        "AI algorithm research for ordinary people",
        "Asks where non-geniuses fit in algorithm research. Li Mu: most people doing AI algorithms are ordinary too.",
    ),
    "0039": (
        "08-applied-verticals",
        "LLMs plus recommendation systems",
        "Asks about large models in recsys. Li Mu says both replacing the rec-model backbone with an LM and doing recommendation purely with language models already have successful apps.",
    ),
    "0040": (
        "06-infra-hardware",
        "PhD in LLM inference chips / infra",
        "A new PhD in inference-chip design worries the real work is algorithm optimization. Li Mu likes the bet: when algorithms change, hardware has to change, so there is always work.",
    ),
    "0042": (
        "09-models-safety",
        "LoRA finetune made a VLM worse",
        "Someone finetuned a multimodal model on hundreds/thousands of labels and got worse results. Li Mu: get more data, or switch models; some models are so over-trained that LoRA does not take well.",
    ),
    "0043": (
        "01-agent-skills",
        "Go deep first, then go wide",
        "Asks whether to specialize or stay broad, and whether traditional backend jobs survive as AI+. Li Mu's personal rule is depth first, then breadth.",
    ),
    "0044": (
        "03-embodied-robotics",
        "Can AI solve the physical world",
        "Argues math/CS are too clean for AI, and asks if AI can really handle messy physics. Li Mu: not yet, though many labs and companies are trying.",
    ),
    "0045": (
        "02-agents",
        "Will agent research still see big inventions",
        "Asks if the agent field still has major innovation left. Li Mu thinks it is moving fast because imagined agent forms are still missing, for example a personal assistant that actually handles chores.",
    ),
    "0046": (
        "03-embodied-robotics",
        "When will robots and LLMs merge",
        "Notes robots and LLMs should complete each other but have split into two tracks. Li Mu: robotics is still stuck on hardware and the cerebellum, not on the brain.",
    ),
    "0047": (
        "10-misc",
        "When AGI arrives and whether to coast",
        "A mix of AGI timelines, how a big-tech worker should invest, and whether to stop learning. Li Mu does not give a date; he trusts human adaptability, and that people will still find something to do.",
    ),
    "0048": (
        "08-applied-verticals",
        "AI for science after AlphaFold",
        "Asks about AI4Science, molecules, AIDD. Li Mu is optimistic but says infrastructure lags: AlphaFold had data and easy verification, which most science problems do not.",
    ),
    "0049": (
        "05-career-hiring",
        "Does BosonAI hire new PhDs",
        "Asks if Boson hires PhD new grads and what profile clears the bar. Li Mu: yes, they interview every day. No bar details.",
    ),
    "0050": (
        "08-applied-verticals",
        "Is business SFT a dead end",
        "An applied algorithm engineer fears foundation models and researchers will erase SFT work. Li Mu: business SFT is still useful, but SFT itself will not be the moat; business understanding and model-to-business fit will.",
    ),
    "0051": (
        "07-learning",
        "Should you still learn old neural-net basics",
        "Someone following Karpathy from scratch asks if pre-transformer material is wasted. Li Mu: learn it anyway, at least to know how the thing works.",
    ),
    "0052": (
        "05-career-hiring",
        "Is management still worth switching into",
        "Asks if big-company management tracks still make sense. Li Mu: relay-the-message managers are likely to be replaced; real management is hard, and people still resist AI as a manager.",
    ),
    "0053": (
        "08-applied-verticals",
        "Polish a vibe-coded product or validate demand",
        "A solo builder has a buggy AI notes app and does not know whether to spend months polishing. Li Mu: first show it to friends and see if they can actually use it.",
    ),
    "0054": (
        "09-models-safety",
        "Future of multimodal",
        "Open question on multimodal. Li Mu: it is important for human-AI interaction, but it is unclear whether it raises model intelligence, which is why some labs deprioritized it.",
    ),
    "0055": (
        "04-research-phd",
        "Skill vs network for research insight",
        "Asks whether insight comes from personal skill or from lab/network. Li Mu: skill sets the floor, network sets the ceiling; worry about the floor first.",
    ),
    "0058": (
        "10-misc",
        "Is this the fake Li Mu",
        "A joke that the account is fake. Li Mu just laughs.",
    ),
    "0059": (
        "08-applied-verticals",
        "Will AI translation replace humans",
        "Asks about AI translation, including messy real-world multimodal/low-latency cases. Li Mu: AI translation can replace about 99% of human work.",
    ),
    "0060": (
        "04-research-phd",
        "Industry frontier vs universities",
        "Worries companies now own the frontier and academia becomes a data feeder. Li Mu: companies can ship what they need; academia is not only about usefulness.",
    ),
    "0061": (
        "01-agent-skills",
        "Where new CS grads should aim",
        "A new CS graduate sees programming change in one year. Li Mu: first get fluent at using agents to maximize your own output.",
    ),
    "0063": (
        "09-models-safety",
        "Where LLMs go next",
        "Asks the important LLM research directions. Li Mu: models running and self-improving in sandboxes, including code execution, computer use on macOS, and world models.",
    ),
    "0064": (
        "01-agent-skills",
        "Do you still need a second programming language",
        "The asker already reviews architecture with AI and wonders if learning C is still needed. Li Mu: one language is enough for now; the human job is reviewing AI code for dumb bugs and bad design detours.",
    ),
    "0065": (
        "09-models-safety",
        "Keep doing multimodal when the market wants agents",
        "Asks if multimodal is still worth it versus agents. Li Mu: multimodal is fine, because humans and agents interact through it.",
    ),
    "0066": (
        "04-research-phd",
        "Is a PhD still worth it versus industry",
        "Worries a PhD is slower and less applied than industry. Li Mu: if you mainly want industry, a PhD is not obviously the best path right now.",
    ),
    "0068": (
        "03-embodied-robotics",
        "World models and embodied AI hype",
        "Asks about the hot and heavily criticized world-model / embodied wave. Li Mu: both are probably required for AI to do blue-collar work, but people may be too optimistic.",
    ),
    "0069": (
        "06-infra-hardware",
        "Is AI hardware the next PhD bet",
        "Someone picking a PhD topic asks if AI hardware will be a boom. Li Mu: there is a market, and China is strong on the hardware side.",
    ),
    "0070": (
        "01-agent-skills",
        "Where humans still beat agents at work",
        "A new hire asks for the human-agent boundary as memory makes experience cheaper. Li Mu flips it: the more you use AI, the more you see its limits, and you learn when it is trustworthy.",
    ),
    "0071": (
        "06-infra-hardware",
        "Embedded and on-device AI demand",
        "Asks if embedded / edge AI is a real need. Li Mu: yes, in cars and phones, and hardware adaptation is a lot of work.",
    ),
    "0072": (
        "09-models-safety",
        "Will alignment drift away from practice",
        "Asks how to think about alignment as models get stronger. Li Mu's feel: recent alignment work is mostly raising IQ, and the resulting reports are already hard for humans to read.",
    ),
    "0073": (
        "02-agents",
        "What RSI actually means",
        "Notes everyone says RSI but does different things. Li Mu: Boson does RSI too, the term is loose, and even AI washing data to train AI can be called RSI.",
    ),
    "0074": (
        "09-models-safety",
        "Are VLMs in a trough versus VLA",
        "Fall recruiting seemed to ignore VLMs; asks if VLA is the better bet. Li Mu: from a practical angle vision is still heavily used in human-agent interaction.",
    ),
    "0075": (
        "04-research-phd",
        "3D/4D scene understanding as a young researcher's bet",
        "A young researcher fears bigger models will cover 3D/4D work. Li Mu is not an expert here but thinks real-world scene understanding/generation is still shallow and far from solved.",
    ),
    "0076": (
        "05-career-hiring",
        "Using AI to talk to engineers",
        "A tech-services person asks how to communicate with engineers, with AI's help. Li Mu: AI can draft and review, but human-to-human talk should stay human; many people hate AI replies.",
    ),
    "0078": (
        "01-agent-skills",
        "Retraining for AI compute / inference",
        "Wants to jump from pure software to AI compute acceleration and doubts learning a language is useful. Li Mu: learning a language is useful, at least so you can read code and give agents good feedback.",
    ),
    "0079": (
        "01-agent-skills",
        "Algorithm engineers vs humanities GPT users",
        "Asks where algorithm engineers beat a humanities grad with GPT. Li Mu: AI multiplies your existing edge by about 10x.",
    ),
    "0080": (
        "06-infra-hardware",
        "Will agents take over LLM training infra",
        "Asks if training-infra work will be automated. Li Mu: agents already handle simple daily work; whole infrastructure design is still beyond them.",
    ),
    "0081": (
        "02-agents",
        "Is agent memory a lasting direction",
        "Asks if agent memory is worth researching for jobs. Li Mu: memory is an important piece of agents; if you like it, go deep.",
    ),
    "0082": (
        "01-agent-skills",
        "Business-algorithm career in a fast-changing market",
        "A third-year master's student on the fall recruiting market feels lost in applied algorithms. Li Mu's test: can you, plus agents, finish work that used to take five people.",
    ),
    "0087": (
        "10-misc",
        "Nostalgia for paper videos",
        "A fan notes they now chat with AI about papers instead of watching Li Mu. Li Mu laughs. No technical claim.",
    ),
    "0091": (
        "10-misc",
        "School-district housing if AI equalizes education",
        "Jokes that school-district apartments are a bad buy if AI democratizes teaching. Li Mu: good education is still scarce, so those homes may still make sense.",
    ),
    "0092": (
        "06-infra-hardware",
        "Is an AI compiler worth learning",
        "Asks if AI compilers are worth the time. Li Mu: it is niche, few teams, and worthwhile if you can find one of those teams.",
    ),
    "0093": (
        "07-learning",
        "How a humanities teacher should use AI",
        "An economics-trained math teacher wants finance/quant skills and asks if they must code. Li Mu's method: pick a topic a day and ask AI twenty questions.",
    ),
    "0095": (
        "04-research-phd",
        "What research is still worth entering",
        "Asks for research topics that are still worth starting now. Li Mu: pick a niche you care about; the field is moving so fast that many places are still under-worked.",
    ),
    "0097": (
        "02-agents",
        "Embodied continual learning vs agent self-evolution",
        "A student is torn between embodied continual learning and agent self-evolution after hearing embodied is foamy. Li Mu: agents apply faster; his own embodied-side work still has a long path to real landing; follow interest.",
    ),
    "0098": (
        "08-applied-verticals",
        "How much AI a founder needs",
        "Asks how much AI a founder must know, and where startups fit if models are general. Li Mu analogizes to cloud ten years ago: AI is now a basic skill, do not compete with the model's mainline, use it to enable other things.",
    ),
    "0099": (
        "10-misc",
        "When AI can sign and take liability",
        "A one-liner about AI taking legal responsibility. Li Mu: insurers may create new products around that.",
    ),
    "0100": (
        "04-research-phd",
        "Will CCF paper counts stay the academic scoreboard",
        "Asks how long paper-count standards last when AI writes papers. Li Mu: standards are sticky, but judging people only by papers is now questionable.",
    ),
    "0197": (
        "01-agent-skills",
        "What an AI application engineer must own in two years",
        "Panic about AI coding: what the market will want later. Li Mu will not forecast two years, but today's signal is people who can own a large chunk of work, now with a pile of agents instead of a 5-10 person team.",
    ),
    "0655": (
        "04-research-phd",
        "AI's shock to academia",
        "Asks how AI hits the academic world. Li Mu feels the shock is large: he already has AI read papers, and he believes many papers are now mainly AI-written.",
    ),
    "0657": (
        "06-infra-hardware",
        "Will AI replace chip designers",
        "Chip-design worry about self-iterating EDA. Li Mu: basic grunt work will go; how far into senior roles is unclear.",
    ),
    "0676": (
        "08-applied-verticals",
        "Search, ads, and recommendation after AI",
        "Asks where search/ads/rec go next. Li Mu: first swap models to transformers; language models doing recsys themselves are also promising.",
    ),
    "0757": (
        "08-applied-verticals",
        "Do vertical models still have a chance",
        "Worries the next foundation-model version will eat any vertical business, including earth science. Li Mu: verticals still have room because the product is not a raw model, it is industry integration and supporting systems.",
    ),
    "0760": (
        "04-research-phd",
        "AI4S protein PhD: research, job, or startup",
        "A protein-design PhD asks where to put energy. Li Mu: interest. If you want something practical, join or start a team; if you want research, stay on research.",
    ),
    "0766": (
        "05-career-hiring",
        "Hiring new grads",
        "Asks if the company hires new grads. Li Mu: they are always hiring.",
    ),
    "0782": (
        "02-agents",
        "Will consumer agents have a GPT moment",
        "Asks about toC agents and a Manus-style GPT moment. Li Mu: yes there will be hits (Manus, 'crayfish'), but their follow-on impact is smaller than GPT.",
    ),
    "0784": (
        "05-career-hiring",
        "Internships at Boson",
        "Asks if Li Mu's company takes interns. Li Mu: Bay Area and Toronto offices both hire interns.",
    ),
    "0786": (
        "08-applied-verticals",
        "Speech as a future interface",
        "Asks about the speech field. Li Mu: Boson works on speech, and he sees it as a natural channel between people and agents.",
    ),
    "0789": (
        "08-applied-verticals",
        "Survival of vertical small models",
        "Asks if small vertical models survive against general models on cost. Li Mu: the model itself may be removed; the remaining value is supporting systems and industry integration.",
    ),
    "0790": (
        "01-agent-skills",
        "Generalists vs specialists after AI coding",
        "Asks who survives if coding already beats ordinary humans: T-shaped generalists or deep specialists. Li Mu: AI has passed humans on implementation speed, not on design, taste, or covering the full problem.",
    ),
    "0793": (
        "08-applied-verticals",
        "Model vendors become like cloud vendors",
        "A comment that domain specialists who build agents will not be replaced. Li Mu: model companies may end up like cloud vendors, a base intelligence utility, with lots of apps on top.",
    ),
    "0986": (
        "07-learning",
        "Please keep lecturing papers",
        "Asks him to keep explaining papers. Li Mu: AI has hit paper talks so hard that he has not figured out a new format.",
    ),
    "0988": (
        "08-applied-verticals",
        "AI for science, pharma, and materials",
        "Asks if fully automatic scientific discovery is near. Li Mu: short-term efficiency gains yes; overturning pharma/materials is hard because of regulation, data cleaning, causality, capability, and interpretability.",
    ),
    "1003": (
        "09-models-safety",
        "Is multimodal only a perception add-on",
        "Asks if multimodal is doomed to be a sidekick of AGI. Li Mu: it is needed for human-agent interaction; there is not much evidence it raises intelligence.",
    ),
    "1010": (
        "04-research-phd",
        "LLM research when pretraining is just scaling",
        "Asks what breakthrough-prone LLM research is left. Li Mu: pretraining is more scaling; post-training algorithms are still complicated.",
    ),
    "1012": (
        "04-research-phd",
        "CV small models during a PhD",
        "A PhD student still working on small CV models asks if that is hopeless. Li Mu: small models are fine; they work well in many small settings.",
    ),
    "1014": (
        "02-agents",
        "How Li Mu sees RSI",
        "Another RSI question. Li Mu: they work on it, but there is no shared definition of which technique counts as RSI.",
    ),
    "1094": (
        "09-models-safety",
        "Capabilities versus alignment / safety",
        "Asks how to balance capability and safety. Li Mu is pessimistic: this is still a race for intelligence, safety work gets obsoleted by the next smarter model, and it often hurts user experience.",
    ),
    "1097": (
        "10-misc",
        "Just saying his name",
        "The comment is only '沐神'. Li Mu replies 'hhh'. No topic content.",
    ),
    "1099": (
        "05-career-hiring",
        "Do LeetCode-style interviews still matter",
        "Asks if algorithm-interview prep is still worth it. Li Mu: many companies still interview that way, and they do not want to suspect the solution was written by AI.",
    ),
    "1188": (
        "01-agent-skills",
        "Deleted question; reply is about reviewing AI code",
        "The original comment was deleted. From Li Mu's reply: you do not have to write code yourself, but you still need to review it, and architecture plus design choices still need a human.",
    ),
    "1189": (
        "01-agent-skills",
        "Deleted question; reply is that junior programmers fade",
        "The original comment was deleted. From Li Mu's reply: basic programmers are disappearing; the surviving path is senior work on complex, large projects.",
    ),
}


def safe_name(text: str, limit: int = 40) -> str:
    text = re.sub(r'[\\/:*?"<>|\s]+', "_", text or "").strip("_")
    text = re.sub(r"_+", "_", text)
    return (text or "user")[:limit]


def main() -> None:
    qa = json.loads(QA_PATH.read_text(encoding="utf-8"))
    by_id = {item["dialogId"]: item for item in qa}

    missing = [did for did in by_id if did not in MAP]
    extra = [did for did in MAP if did not in by_id]
    if missing or extra:
        raise SystemExit(f"map mismatch missing={missing} extra={extra}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    cat_meta = {folder: (title, desc) for folder, title, desc in CATEGORIES}
    grouped: dict[str, list[dict]] = {folder: [] for folder, _, _ in CATEGORIES}

    for item in qa:
        folder, title, about = MAP[item["dialogId"]]
        replies = item["author_replies"]
        reply_block = "\n\n".join(r["content"] for r in replies)
        body = "\n".join(
            [
                f"Topic: {cat_meta[folder][0]}",
                f"Category: {folder}",
                f"Dialog: {item['dialogId']}",
                f"Asker: {item['asker']}",
                f"Comment ID: {item['commentId']}",
                f"Source: comments/{item['file']}",
                f"Title: {title}",
                "",
                "About",
                about,
                "",
                "Question",
                item["question"],
                "",
                "Li Mu",
                reply_block,
                "",
            ]
        )
        folder_path = OUT_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        fname = f"{item['dialogId']}_{safe_name(item['asker'])}.txt"
        (folder_path / fname).write_text(body, encoding="utf-8")
        grouped[folder].append(
            {
                "dialogId": item["dialogId"],
                "asker": item["asker"],
                "file": fname,
                "title": title,
                "about": about,
                "source": item["file"],
                "question": item["question"],
                "authorReplies": [r["content"] for r in replies],
            }
        )

    index_lines = [
        "Li Mu AMA — author-replied comments, grouped into 10 topics",
        f"Threads: {len(qa)}",
        f"Author replies: {sum(len(x['author_replies']) for x in qa)}",
        "",
        "These 10 buckets came from reading every parent comment he replied to.",
        "Most questions cluster around skills-with-agents, research/PhD, jobs, infra,",
        "learning paths, vertical applications, and model/safety debates.",
        "Leftovers (jokes, housing, liability, empty pings) go in misc.",
        "",
    ]
    catalog = {"totalThreads": len(qa), "categories": []}
    for folder, title, desc in CATEGORIES:
        items = grouped[folder]
        index_lines.append(f"{folder}  {title}  ({len(items)})")
        index_lines.append(f"  {desc}")
        for row in items:
            index_lines.append(f"  - {row['dialogId']} {row['asker']}: {row['title']}")
        index_lines.append("")
        cat_path = OUT_DIR / folder / "_category.txt"
        cat_lines = [
            f"{title}",
            desc,
            f"Count: {len(items)}",
            "",
        ]
        for row in items:
            cat_lines.append(f"{row['dialogId']}  {row['asker']}")
            cat_lines.append(f"  {row['title']}")
            cat_lines.append(f"  {row['about']}")
            cat_lines.append("")
        cat_path.write_text("\n".join(cat_lines), encoding="utf-8")
        catalog["categories"].append(
            {
                "id": folder,
                "title": title,
                "description": desc,
                "count": len(items),
                "threads": items,
            }
        )

    (OUT_DIR / "00_index.txt").write_text("\n".join(index_lines), encoding="utf-8")
    (OUT_DIR / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(qa)} summaries into {OUT_DIR}")
    for folder, _, _ in CATEGORIES:
        print(f"  {folder}: {len(grouped[folder])}")


if __name__ == "__main__":
    main()
