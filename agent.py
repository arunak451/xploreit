import asyncio
import os
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, groq, silero
from rag import retrieve, build_knowledge_base

load_dotenv()

# Build once at startup
print("Loading knowledge base...")
build_knowledge_base()
kb_context = retrieve("XploreiT Corp courses admission fees")
print("Knowledge base ready!")


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=deepgram.TTS(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            model="aura-asteria-en"
        ),
    )

    agent = Agent(
        instructions=f"""You are a helpful AI assistant for XploreiT Corp,
        a software training institute in Coimbatore.
        Your job is to:
        1. Greet the student warmly
        2. Ask for their name and which course they are interested in
        3. Answer questions about courses, fees, admission process
        4. Be friendly and professional
        Knowledge Base:
        {kb_context}
        Keep responses short and clear for phone calls.
        Speak in English or Tamil based on student preference.
        """
    )

    await session.start(
        room=ctx.room,
        agent=agent
    )

    await ctx.wait_for_participant()

    try:
        await session.generate_reply(
            instructions="Greet the student warmly and introduce yourself as XploreiT Corp AI assistant."
        )
    except Exception as e:
        print(f"Error: {e}")

    try:
        await asyncio.sleep(600)
    except Exception:
        pass

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
