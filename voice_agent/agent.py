from dotenv import load_dotenv
import asyncio
import os
import logging
import traceback
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobRequest
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    silero
    
)
from livekit.agents.llm import ChatMessage
import livekit.agents.llm as livekit_llm
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
# from livekit.agents import ChatContext
load_dotenv()


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")





class Assistant(Agent):
    def __init__(self,session:AgentSession,index):
        base_dir = os.path.dirname(os.path.abspath(__file__))  # points to voice_agent/
        prompt_path = os.path.join(base_dir, "prompt_template.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            instructions = f.read()
        super().__init__(instructions=instructions)
        
        self.index = index
        self._session=session
        self.interaction_count = 0
        
        async def llm_node(
        self,
        chat_ctx: livekit_llm.ChatContext,
        tools: list[livekit_llm.FunctionTool],
        ):
            self.interaction_count += 1

            chat_ctx_to_use = livekit_llm.ChatContext()

    # 1. Get user query (latest message)
            user_query = ""
            if chat_ctx.items and isinstance(chat_ctx.items[-1], ChatMessage) and chat_ctx.items[-1].role == "user":
                user_query = chat_ctx.items[-1].text_content or ""

            context = instructions + "\n\n"
            if user_query.strip():
                docs = self.index.similarity_search(user_query, k=5)
                for doc in docs:
                    context += doc.page_content + "\n"
            
            chat_ctx_to_use.items.append(ChatMessage(role="system", content=[context]))
            conversation_history = [
            msg for msg in chat_ctx.items if msg.role != "system"
            ][-3:]
            chat_ctx_to_use.items.extend(conversation_history)

            print("======== Final chat_ctx_to_use ========")
            for msg in chat_ctx_to_use.items:
                print(f"{msg.role.upper()}: {msg.content}")

            first_chunk = True
            async for chunk in Agent.default.llm_node(self, chat_ctx_to_use, tools):
                # if first_chunk:
                    # llm_response_received_time = time.time()
                    # llm_processing_time = llm_response_received_time - llm_query_sent_time
                # logger.info(f"LLM query received at {llm_response_received_time:.2f} (Processing time: {llm_processing_time:.2f} seconds)")
                # logger.info(f"TTS start at {llm_response_received_time:.2f}")
                # first_chunk = False
                yield chunk
    

async def request_fnc(req: JobRequest):
    # accept the job request
    await req.accept(
        # the agent's name (Participant.name), defaults to ""
        name="agent",
        # the agent's identity (Participant.identity), defaults to "agent-<jobid>"
        identity="identity",
        # attributes to set on the agent participant upon join
        attributes={"myagent": "rocks"},
    )
async def entrypoint(ctx: agents.JobContext):
  try:
    from rag_utils import load_faiss_vectorstore
    try:
        vectorstore = load_faiss_vectorstore()
        print("[Agent] Vectorstore loaded successfully.", flush=True)
    except Exception as e:
        print("[ERROR] Failed to load vectorstore", flush=True)
        traceback.print_exc()

    await ctx.connect()
    

    try:
            session = AgentSession(
                stt=deepgram.STT(model="nova-3", language="multi"),
                llm=openai.LLM(model="gpt-4o"),
                tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
                vad=silero.VAD.load(),
                # turn_detection=MultilingualModel(),
            )
    except Exception as e:
            logging.error(f"Failed to initialize session: {str(e)}")
            return
    

    try:
        agent = Assistant(session=session, index=vectorstore)
    except Exception as e:
        logging.error(f"Failed to initialize Assistant: {str(e)}")
        return


    try:
      await session.start(
          room=ctx.room,
              agent=agent,
              room_input_options=RoomInputOptions(),
            )
    except Exception as e:
          logging.error(f"Failed to start session: {str(e)}")
          return
    
    await session.generate_reply(
        instructions="Hi, welcome to Unbroker"
    )
  
  except Exception as e:
      logging.error(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint,request_fnc=request_fnc))