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
