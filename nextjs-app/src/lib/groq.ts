import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY || "",
});

export async function getAIReview(code: string, language: string, problemStatement: string) {
  try {
    const prompt = `
      Act as an expert code reviewer. Review the following ${language} code submission for a programming problem.
      
      Problem Statement:
      ${problemStatement}
      
      User's Code:
      \`\`\`${language}
      ${code}
      \`\`\`
      
      Provide your review in the following format (use Markdown):
      
      ### 📊 Overall Rating
      Rate the code out of 10 based on correctness, readability, and efficiency.
      
      ### ⏱️ Time & Space Complexity
      Analyze the Big-O time and space complexity of the solution.
      
      ### 💡 Key Improvements (Tips)
      Provide 1-3 specific, actionable tips to improve the code. Focus on:
      1. Edge cases they might have missed
      2. More idiomatic ways to write this in ${language}
      3. Potential optimizations
      
      Keep the review concise, encouraging, and highly technical.
    `;

    const chatCompletion = await groq.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      model: "llama-3.1-8b-instant", // Updated from deprecated llama3-8b-8192
    });

    const text = chatCompletion.choices[0]?.message?.content || "";
    
    return { success: true, review: text };
  } catch (error) {
    console.error("Groq API Error:", error);
    return { success: false, error: "Failed to generate AI review. Please try again." };
  }
}

const VALID_TOPICS = [
  "Arrays", "Strings", "Linked Lists", "Trees", "Graphs", "Dynamic Programming",
  "Greedy", "Backtracking", "Sorting", "Searching", "Binary Search", "Hash Maps",
  "Stacks", "Queues", "Heaps", "Recursion", "Math", "Two Pointers", "Sliding Window",
  "Bit Manipulation", "Tries", "Union Find", "Segment Trees", "Matrix",
];

export async function getTopicTags(name: string, statement: string): Promise<string[]> {
  try {
    const prompt = `You are an expert competitive programmer. Given the following programming problem, assign the most relevant topic tags from the list below.

Problem Name: ${name}
Problem Description: ${statement.substring(0, 1500)}

Valid Topics (choose only from this list):
${VALID_TOPICS.join(", ")}

Rules:
- Return ONLY a JSON array of strings, nothing else.
- Choose 1 to 4 of the most relevant topics.
- Do not add topics not in the valid list.
- Example output: ["Arrays", "Hash Maps"]

Output:`;

    const chatCompletion = await groq.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      model: "llama-3.1-8b-instant",
    });

    const text = chatCompletion.choices[0]?.message?.content?.trim() || "[]";
    // Extract JSON array from response
    const match = text.match(/\[[\s\S]*?\]/);
    if (!match) return [];

    const parsed = JSON.parse(match[0]);
    if (!Array.isArray(parsed)) return [];

    // Filter to only valid topics
    return parsed.filter((t: unknown) =>
      typeof t === "string" && VALID_TOPICS.includes(t)
    );
  } catch (error) {
    console.error("Groq Topic Tags Error:", error);
    return [];
  }
}

export async function getAIHint(
  problemStatement: string,
  currentCode: string,
  language: string,
  hintLevel: 1 | 2 | 3
): Promise<{ success: boolean; hint?: string; error?: string }> {
  try {
    const levelDescriptions: Record<number, string> = {
      1: "Give a high-level conceptual hint. Do NOT mention specific algorithms or code. Just guide their thinking about what the problem is asking. 2-3 sentences max.",
      2: "Give an algorithmic hint. Mention the type of data structure or algorithm that could work (e.g., 'think about using a hash map' or 'a sliding window might help here'). Do NOT give code. 3-4 sentences max.",
      3: "Give a near-solution hint. Describe the key steps of the solution approach in plain English. You may mention pseudocode but do NOT write actual code. 4-5 sentences max.",
    };

    const hasCode = currentCode.trim().length > 50;

    const prompt = `You are a helpful coding mentor helping a student solve a programming problem.

Problem Statement:
${problemStatement}

${hasCode ? `Student's Current Code (${language}):\n\`\`\`${language}\n${currentCode.slice(0, 800)}\n\`\`\`` : "The student hasn't written much code yet."}

Hint Level ${hintLevel}/3: ${levelDescriptions[hintLevel]}

Important rules:
- Be encouraging and Socratic — guide, don't solve
- Do NOT write actual code
- Keep the response concise and focused
- Format using Markdown (bold key terms)`;

    const chatCompletion = await groq.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      model: "llama-3.1-8b-instant",
    });

    const text = chatCompletion.choices[0]?.message?.content || "";
    return { success: true, hint: text };
  } catch (error) {
    console.error("Groq Hint Error:", error);
    return { success: false, error: "Failed to generate hint. Please try again." };
  }
}
