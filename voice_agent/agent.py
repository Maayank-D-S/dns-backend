from dotenv import load_dotenv
import logging
import traceback
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
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
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
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
              if self.interaction_count <= 2:
                  # Use original chat_ctx with full instructions for first two interactions
                  chat_ctx_to_use = chat_ctx
              else:
                  # Use short system message and last three messages (last two user messages + assistant response)
                  conversation_history = chat_ctx.items[-3:]  # Last 3 messages: user(n-1), assistant(n-1), user(n)
                  chat_ctx_to_use = livekit_llm.ChatContext()
                  chat_ctx_to_use.items = conversation_history


              if chat_ctx.items and isinstance(chat_ctx.items[-1], ChatMessage) and chat_ctx.items[-1].role == "user":
                    user_query = chat_ctx.items[-1].text_content or ""
                    if user_query.strip():
                        # Check if the query contains any trigger words (case-insensitive)
                      # if any(trigger.lower() in user_query.lower() for trigger in self.TRIGGER_WORDS):
                      # logger.info(f"Performing RAG for query: {user_query[:50]}...")
                    # Start timing RAG
                    
                    # Fetch RAG context
                        # retriever = self.index.as_retriever()
                        # nodes = await retriever.aretrieve(user_query)
                        docs =  index.similarity_search(user_query, k=15)
                        context = []
                        context = "Relevant context from documents:\n"
                        for doc in docs:
                            context.append(doc.page_content)
                        

                        if chat_ctx_to_use.items and isinstance(chat_ctx_to_use.items[0], ChatMessage) and          chat_ctx_to_use.items[0].role == "system":
                            chat_ctx_to_use.items[0].content.append(context)
                        else:
                            chat_ctx_to_use.items.insert(0, ChatMessage(role="system", content=[context]))

                    # Inject into system message of the chat context being used
                        if chat_ctx_to_use.items and isinstance(chat_ctx_to_use.items[0], ChatMessage) and          chat_ctx_to_use.items[0].role == "system":
                            chat_ctx_to_use.items[0].content.append(context)
                        else:
                            chat_ctx_to_use.items.insert(0, ChatMessage(role="system", content=[context]))

                    # rag_time = time.time() - rag_start_time
                    # logger.info(f"RAG query processed in {rag_time:.2f} seconds for query: {user_query[:50]}...")
                            print(f"[RAG] Injected context: {context[:100].replace(chr(10), ' | ')}...")
                    # else:
                    #     # logger.info(f"Skipping RAG for query: {user_query[:50]}...")
              

              first_chunk = True
              async for chunk in Agent.default.llm_node(self, chat_ctx_to_use, tools, model_settings):
                # if first_chunk:
                    # llm_response_received_time = time.time()
                    # llm_processing_time = llm_response_received_time - llm_query_sent_time
                # logger.info(f"LLM query received at {llm_response_received_time:.2f} (Processing time: {llm_processing_time:.2f} seconds)")
                # logger.info(f"TTS start at {llm_response_received_time:.2f}")
                # first_chunk = False
                yield chunk
    


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
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))