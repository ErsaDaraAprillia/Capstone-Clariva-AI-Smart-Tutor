def build_comparison_prompts(question, domain="general"):
    """
    Generate 3 prompts using different APE techniques for the same question.
    Few-shot examples are dynamically generated based on domain/topic category.
    """

    # ── Auto-detect domain dari keyword di question ─────────────
    q_lower = question.lower()

    if any(k in q_lower for k in ["code", "program", "python", "function",
                                    "algorithm", "recursion", "loop", "class",
                                    "api", "database", "sql", "javascript"]):
        detected_domain = "programming"
    elif any(k in q_lower for k in ["history", "war", "revolution", "empire",
                                      "civilization", "century", "president",
                                      "battle", "treaty"]):
        detected_domain = "history"
    elif any(k in q_lower for k in ["math", "calculus", "algebra", "equation",
                                      "geometry", "probability", "statistics",
                                      "theorem", "derivative", "integral"]):
        detected_domain = "math"
    elif any(k in q_lower for k in ["biology", "cell", "dna", "evolution",
                                      "photosynthesis", "immune", "organ",
                                      "genetics", "species", "ecosystem"]):
        detected_domain = "biology"
    elif any(k in q_lower for k in ["physics", "force", "energy", "gravity",
                                      "quantum", "wave", "electron", "atom",
                                      "velocity", "mass"]):
        detected_domain = "physics"
    elif any(k in q_lower for k in ["machine learning", "ai", "neural",
                                      "deep learning", "model", "training",
                                      "dataset", "classification", "regression"]):
        detected_domain = "ai_ml"
    else:
        detected_domain = "general"

    # ── Domain-specific few-shot examples ───────────────────────
    few_shot_examples = {
        "programming": """
EXAMPLE 1:
Q: What is a function in programming?
A: A function is a reusable block of code that performs a specific task.
   Think of it like a recipe — you define it once, then "call" it whenever needed.
   Example in Python:
   def greet(name):
       return f"Hello, {name}!"
   greet("Alice")  # → "Hello, Alice!"
   Functions reduce repetition and make code easier to maintain.

EXAMPLE 2:
Q: What is a loop?
A: A loop repeats a block of code multiple times.
   A `for` loop runs a set number of times; a `while` loop runs until a condition is false.
   Example: `for i in range(5): print(i)` prints 0 through 4.
   Use loops to avoid writing the same code over and over.""",

        "history": """
EXAMPLE 1:
Q: What caused World War I?
A: WWI was triggered by Archduke Franz Ferdinand's assassination in 1914,
   but the deeper causes were nationalism, militarism, imperial rivalries,
   and a web of alliances that turned a regional conflict into a global war.
   The MAIN acronym captures it: Militarism, Alliances, Imperialism, Nationalism.

EXAMPLE 2:
Q: What was the Cold War?
A: The Cold War (1947–1991) was a geopolitical tension between the US and USSR —
   not a direct war, but a competition of ideology (capitalism vs communism),
   nuclear arms buildup, proxy wars (Korea, Vietnam), and the space race.
   It ended with the Soviet Union's collapse in 1991.""",

        "math": """
EXAMPLE 1:
Q: What is the Pythagorean theorem?
A: In a right triangle, a² + b² = c², where c is the hypotenuse (longest side).
   Example: if a=3, b=4, then c=√(9+16)=√25=5.
   It's used in navigation, construction, and computer graphics.

EXAMPLE 2:
Q: What is a derivative?
A: A derivative measures how fast a function changes at any given point — it's
   the instantaneous rate of change. If f(x) = x², then f'(x) = 2x.
   At x=3, the slope of the curve is 6. Used in physics, economics, and optimization.""",

        "biology": """
EXAMPLE 1:
Q: How does DNA replication work?
A: DNA replication copies the double helix before cell division.
   The enzyme helicase unzips the two strands; DNA polymerase builds
   a new complementary strand on each. Result: two identical DNA molecules.
   Key rule: A pairs with T, and C pairs with G.

EXAMPLE 2:
Q: What is natural selection?
A: Natural selection is evolution's core mechanism — individuals with traits
   better suited to their environment survive and reproduce more.
   Over generations, those traits become more common in the population.
   Darwin observed this in finch beak variations across the Galápagos Islands.""",

        "physics": """
EXAMPLE 1:
Q: What is Newton's second law?
A: F = ma — Force equals mass times acceleration.
   If you push a 2kg box with 10N of force, it accelerates at 5 m/s².
   Heavier objects need more force to accelerate at the same rate.

EXAMPLE 2:
Q: What is the law of conservation of energy?
A: Energy cannot be created or destroyed — only converted between forms.
   A falling ball converts potential energy to kinetic energy.
   Total energy in a closed system always stays constant.""",

        "ai_ml": """
EXAMPLE 1:
Q: What is supervised learning?
A: Supervised learning trains a model on labeled data — input-output pairs.
   Example: show 10,000 images labeled "cat" or "dog"; the model learns
   the pattern and can classify new images it has never seen.
   Common algorithms: Linear Regression, Decision Trees, Neural Networks.

EXAMPLE 2:
Q: What is overfitting?
A: Overfitting is when a model memorizes training data instead of learning
   general patterns — it performs great on training data but poorly on new data.
   Fix: use more training data, dropout, or regularization techniques.""",

        "general": """
EXAMPLE 1:
Q: What is inflation?
A: Inflation is the rate at which prices rise over time, reducing purchasing power.
   If inflation is 5%, a $100 basket of goods costs $105 next year.
   Caused by excess money supply, high demand, or supply chain issues.
   Central banks manage it by adjusting interest rates.

EXAMPLE 2:
Q: What is the scientific method?
A: The scientific method is a systematic process for testing ideas:
   Observe → Question → Hypothesis → Experiment → Analyze → Conclude.
   It ensures conclusions are based on evidence, not assumption.
   Every experiment must be reproducible to be scientifically valid."""
    }

    examples = few_shot_examples.get(detected_domain, few_shot_examples["general"])

    # ════════════════════════════════════════════════════════════
    # TECHNIQUE 1: ZERO-SHOT
    # No examples, no structure — raw minimal prompt
    # ════════════════════════════════════════════════════════════
    zero_shot = f"""Explain the following topic clearly and concisely:
    {question}"""

    # ════════════════════════════════════════════════════════════
    # TECHNIQUE 2: FEW-SHOT (dynamic examples per domain)
    # Pattern-match output style from 2 domain-relevant examples
    # ════════════════════════════════════════════════════════════
    few_shot = f"""Here are two examples of high-quality topic explanations \
      in the {detected_domain} domain:
      {examples}

---
Now explain the following in the same clear, example-driven style:

Q: {question}
A:"""

    # ════════════════════════════════════════════════════════════
    # TECHNIQUE 3: CHAIN-OF-THOUGHT (explicit reasoning steps)
    # Forces step-by-step decomposition before final answer
    # ════════════════════════════════════════════════════════════
    cot_prompt = f"""Work through the following topic using structured \
      step-by-step reasoning.

Topic: {question}

Follow these reasoning steps explicitly:

Step 1 — Define it precisely:
Give the clearest, most accurate definition possible.

Step 2 — Break down the core components:
What are the 2-3 key parts or mechanisms that make this work?

Step 3 — Walk through a concrete example:
Show a specific real-world or worked example from start to finish.

Step 4 — Explain why it matters:
What problem does this solve? Why is it important to understand?

Step 5 — Address a common misconception:
What do most people get wrong or confused about on this topic?

Now work through each step carefully, then give your complete answer below."""

    return zero_shot, few_shot, cot_prompt, detected_domain