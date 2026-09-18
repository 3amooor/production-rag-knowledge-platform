import { FormEvent, useEffect, useState } from "react";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const demoMode = import.meta.env.VITE_DEMO_MODE === "true";

type Workspace = { id: string; name: string; slug: string };
type Document = { id: string; filename: string; status: string; size_bytes: number };
type Citation = { filename: string; excerpt: string; score: number };
type Answer = { assistant_message: { content: string; citations: Citation[] } };

const demoWorkspace: Workspace = {
  id: "portfolio-demo",
  name: "Product Knowledge",
  slug: "product-knowledge",
};
const demoDocuments: Document[] = [
  {
    id: "architecture-source",
    filename: "platform-architecture.md",
    status: "READY",
    size_bytes: 8_742,
  },
  {
    id: "security-source",
    filename: "security-model.md",
    status: "READY",
    size_bytes: 4_216,
  },
];

async function api<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = Array.isArray(payload.detail)
      ? payload.detail.map((item: { msg?: string }) => item.msg ?? "Invalid input.").join(" ")
      : payload.detail;
    throw new Error(typeof detail === "string" ? detail : "The request could not be completed.");
  }
  return response.json() as Promise<T>;
}

export function App() {
  const [token, setToken] = useState(
    localStorage.getItem("rag_access_token") ?? (demoMode ? "portfolio-demo" : ""),
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>(demoMode ? [demoWorkspace] : []);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(
    demoMode ? demoWorkspace : null,
  );
  const [documents, setDocuments] = useState<Document[]>(demoMode ? demoDocuments : []);
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceSlug, setWorkspaceSlug] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [notice, setNotice] = useState(
    demoMode
      ? "Interactive portfolio demo — no data leaves your browser."
      : "Welcome. Connect a workspace to begin.",
  );

  const loadWorkspaces = async () => {
    if (demoMode) return;
    const items = await api<Workspace[]>("/workspaces", token);
    setWorkspaces(items);
    setActiveWorkspace((current) => current ?? items[0] ?? null);
  };

  const loadDocuments = async (workspace: Workspace) => {
    if (demoMode) return;
    setDocuments(await api<Document[]>(`/workspaces/${workspace.id}/documents`, token));
  };

  useEffect(() => {
    if (!token) return;
    void loadWorkspaces().catch((error: Error) => setNotice(error.message));
  }, [token]);

  useEffect(() => {
    if (activeWorkspace) void loadDocuments(activeWorkspace).catch((error: Error) => setNotice(error.message));
  }, [activeWorkspace]);

  const authenticate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (demoMode) {
      setToken("portfolio-demo");
      setNotice("Portfolio demo opened.");
      return;
    }
    try {
      const route = isRegistering ? "/auth/register" : "/auth/login";
      const credentials = await api<{ access_token: string }>(route, undefined, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("rag_access_token", credentials.access_token);
      setToken(credentials.access_token);
      setNotice(isRegistering ? "Account created successfully." : "Signed in successfully.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Sign-in failed.");
    }
  };

  const createWorkspace = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      if (demoMode) {
        const workspace = {
          id: `demo-${Date.now()}`,
          name: workspaceName,
          slug: workspaceSlug,
        };
        setWorkspaces((items) => [workspace, ...items]);
        setActiveWorkspace(workspace);
        setDocuments([]);
        setWorkspaceName("");
        setWorkspaceSlug("");
        setNotice(`Demo workspace “${workspace.name}” created in this browser.`);
        return;
      }
      const workspace = await api<Workspace>("/workspaces", token, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: workspaceName, slug: workspaceSlug }),
      });
      setWorkspaces((items) => [workspace, ...items]);
      setActiveWorkspace(workspace);
      setWorkspaceName("");
      setWorkspaceSlug("");
      setNotice(`Workspace “${workspace.name}” created.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Workspace creation failed.");
    }
  };

  const upload = async (file: File) => {
    if (!activeWorkspace) return;
    if (demoMode) {
      setDocuments((items) => [
        {
          id: `demo-document-${Date.now()}`,
          filename: file.name,
          status: "READY",
          size_bytes: file.size,
        },
        ...items,
      ]);
      setNotice(`${file.name} indexed in demo mode.`);
      return;
    }
    const data = new FormData();
    data.append("upload", file);
    try {
      await api(`/workspaces/${activeWorkspace.id}/documents`, token, { method: "POST", body: data });
      await loadDocuments(activeWorkspace);
      setNotice(`${file.name} queued for indexing.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Upload failed.");
    }
  };

  const ask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!activeWorkspace || !question.trim()) return;
    if (demoMode) {
      setAnswer({
        assistant_message: {
          content:
            "The platform uses workspace-scoped hybrid retrieval: pgvector provides dense candidates, PostgreSQL full-text search provides lexical candidates, and reciprocal-rank fusion combines both before returning a cited answer.",
          citations: [
            {
              filename: "platform-architecture.md",
              excerpt:
                "Dense and lexical queries apply the authorized workspace ID inside SQL before reciprocal-rank fusion.",
              score: 0.0325,
            },
          ],
        },
      });
      setNotice("Demo answer generated from workspace sources.");
      return;
    }
    try {
      const conversation = await api<{ id: string }>(`/workspaces/${activeWorkspace.id}/conversations`, token, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: question.slice(0, 80) }),
      });
      const result = await api<Answer>(
        `/workspaces/${activeWorkspace.id}/conversations/${conversation.id}/messages`,
        token,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: question }) },
      );
      setAnswer(result);
      setNotice("Answer generated from workspace sources.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Question failed.");
    }
  };

  if (!token) {
    return <main className="auth"><section><p className="eyebrow">RETRIEVAL, GROUNDED</p><h1>Your knowledge, ready to answer.</h1><p>Bring Markdown and text sources into a private, workspace-scoped retrieval system.</p></section><form onSubmit={authenticate}><h2>{isRegistering ? "Create account" : "Sign in"}</h2><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} required /></label><button>{isRegistering ? "Create account" : "Enter platform"}</button><button className="text-button" type="button" onClick={() => setIsRegistering((value) => !value)}>{isRegistering ? "Already have an account? Sign in" : "New here? Create an account"}</button><p className="notice">{notice}</p></form></main>;
  }

  return <main className="app"><aside><p className="eyebrow">RAG PLATFORM</p><h1>Knowledge base</h1><nav>{workspaces.map((workspace) => <button className={workspace.id === activeWorkspace?.id ? "selected" : ""} key={workspace.id} onClick={() => setActiveWorkspace(workspace)}>{workspace.name}<small>{workspace.slug}</small></button>)}</nav><form onSubmit={createWorkspace}><input aria-label="Workspace name" placeholder="Workspace name" value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} required /><input aria-label="Workspace slug" placeholder="workspace-slug" pattern="[a-z0-9]+(-[a-z0-9]+)*" value={workspaceSlug} onChange={(event) => setWorkspaceSlug(event.target.value)} required /><button>Create workspace</button></form><button className="quiet" onClick={() => { localStorage.removeItem("rag_access_token"); setToken(""); }}>Sign out</button></aside><section className="content"><header><div><p className="eyebrow">{activeWorkspace?.slug ?? "NO WORKSPACE"}</p><h2>{activeWorkspace?.name ?? "Create your first workspace"}</h2></div><p className="notice">{notice}</p></header><div className="grid"><article><h3>Sources</h3><label className="upload">Upload text or Markdown<input type="file" accept="text/plain,text/markdown,.txt,.md" onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); }} /></label><ul className="documents">{documents.map((document) => <li key={document.id}><strong>{document.filename}</strong><span>{document.status} · {Math.ceil(document.size_bytes / 1024)} KB</span></li>)}</ul></article><article className="chat"><h3>Ask your knowledge base</h3><form onSubmit={ask}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What would you like to know?" /><button>Ask question</button></form>{answer && <div className="answer"><p>{answer.assistant_message.content}</p>{answer.assistant_message.citations.map((citation, index) => <blockquote key={`${citation.filename}-${index}`}><strong>{citation.filename}</strong>{citation.excerpt}</blockquote>)}</div>}</article></div></section></main>;
}
