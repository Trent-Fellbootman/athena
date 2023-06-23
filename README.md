# Athena AI

## Important notice: This project is being rebased onto OpenNN. Backend abstractions are expected to use OpenNN instead.

## Important notice: This project is under development, pending rebasement onto OpenNN. Current code is considered obsolete.

## Overview

Athena AI is a framework for developing complex AI systems.
It supports multi-modality, external API integration,
parallelism, error correction, and more.
It is designed to be the PyTorch, Tensorflow and JAX for the
nascent, emerging field of AI: automated prompting.

Possible use cases of this framework include:

- AI-native applications and OS;
- AI-based applications (e.g., AI-based game engines)
- AI assistant for consumer applications that integrates
AI into the application's functionalities (e.g., Siri).

## Core Concepts

There are several core concepts introduced in Athena AI:

### Automated AI System (AAIS)

An AAIS is a system where multiple processes work together
concurrently to accomplish a task.
Processes in an AAIS are usually intelligent, using AIs
such as GPT-4, ChatGPT, etc. as their backends.

Processes in an AAIS communicate with each other and interfaces
with the environment via APIs.

### Process

A process in an AAIS is a stateful object with a life cycle
which communicates with other processes and is able to make
API calls in order to accomplish a certain task.
Many processes in an AAIS use AIs as their backends.

### API

An API is an interface between a process and the environment.
By making API calls, a process can have capabilities such as:

- Reading and writing files;
- Browsing the Internet;
- Interacting with the user;
- Spawning new processes;
- Access other software, e.g., Python.

### AI Backend

An AI backend in an AAIS is analogous to a piece of hardware
in a traditional computer.
AI backends powers the intelligence of AAIS processes, allowing them
to cooperate and accomplish complex tasks.

Typically, AI backends are deep learning models that produce outputs
given inputs.
Examples include: ChatGPT; GPT-4; etc.

It is worth mentioning that many AI backends that are designed
to accomplish one task only (i.e., they are not for general purpose)
are typically considered APIs, rather than AI backends.
Examples include: image classification models; text to speech;
YOLO v5; DALL E 2, etc.

### Functional

A functional is a piece of program that transforms inputs to outputs,
without side effects (e.g., print statements).
Think of a functional as a mapping from the input set to the output set.

Athena AI extends the concept of functional to include
stochasticity: a functional can be stochastic, meaning that
feeding it with the same input multiple times may produce
different outputs (due to the inherited stochasticity of LLMs, for example).
However, such stochasticity is the result of inherited randomness
in the functionals themselves; functionals are still stateless and
have no side effects.

An example of a functional is a summarizer: input a piece of text,
use an AI backend (e.g., ChatGPT) to produce a summarized version.


## Code Structure

### Naming

All public classes, methods, etc.
begin with the prefix "AAIS" (Automated AI System).

### Modules

Currently, there are 7 modules in the package:

- `core` contains the base classes that models the bare bone
Automated AI System (AAIS), the core concept of this framework.
- `api_integration` defines classes and methods to integrate APIs (whether
intelligent or non-intelligent) with an AAIS.
- `backend_abstraction` defines classes that abstracts
AI backends (e.g., ChatGPT, GPT-4, etc.).
- `functional` defines basic AI functionals (e.g., summarization,
transformation, selection, etc.).
- `task_completion` defines classes AAIS processes designed
to work with other processes and accomplish complex tasks.
- `thinking_language` contains abstractions related to
thinking languages.
