from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

def run_research_pipeline(topic: str) -> dict:

    state = {}

    #search agent working
    print("\n"+"="*50)
    print("Step 1- search agent is working ...")
    print("="*50+"\n")

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages" : [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_result"] = search_result["messages"][-1].content

    print("\n Search Result:", state["search_result"])

    #reader agent working
    print("\n"+"="*50)
    print("Step 2- Reader agent is scraping top resources ...")
    print("="*50+"\n")

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_result'][:800]}"
        )]
    })
    state['scraped_content'] = reader_result["messages"][-1].content

    print("\n Scraped Content:", state["scraped_content"])

    #writer chain working
    print("\n"+"="*50)
    print("Step 3- Writer is generating the final report ...")
    print("="*50+"\n")

    research_combine = (
        f"Search Results:\n{state['search_result']}\n\n"
        f"Detailed Scraped Content:\n{state['scraped_content']}"
    )
    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combine
    })

    print("\n Final Report\n", state["report"])

    #critics report
    print("\n"+"="*50)
    print("Step 4- Critics are reviewing the final report ...")
    print("="*50+"\n")

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\n Critics Review\n", state["feedback"])

    return state

if __name__ == "__main__":
    topic = input("\nEnter a research topic: ")
    run_research_pipeline(topic)
