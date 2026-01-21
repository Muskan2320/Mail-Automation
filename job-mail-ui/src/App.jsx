import { useState } from 'react'

function App() {
  const [jdText, setJdText] = useState("");
  const [resumeFile, setResumeFile] = useState(null);

  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");

  const handleGenerate = async () => {
    if (!jdText) {
      alert("Please enter Job Description");
      return;
    }

    setGenerating(true);
    setMessage("");

    const formData = new FormData();
    formData.append("jd_text", jdText);
    if (resumeFile) {
      formData.append("resume_file", resumeFile);
    }

    try {
      const res = await fetch("http://localhost:8000/generate-email", {
        method: "POST",
        body: formData
      });
    
      const data = await res.json();
    
      if (!res.ok) {
        throw new Erro(data.detail || "Failed to generate email");
      }

      setRecipient(data.data.recipient || "");
      setSubject(data.data.subject || "");
      setBody(data.data.body || "");
      
      setMessage("Email generated successfully!");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleSend = async () => {
    if(!recipient || !subject || !body) {
      alert("Recipient, Subject and Body are required to send email");
      return;
    }

    setSending(true);
    setMessage("");

    const formData = new FormData();
    formData.append("recipient", recipient);
    formData.append("subject", subject);
    formData.append("body", body);
    if (resumeFile) {
      formData.append("resume_file", resumeFile);
    }

    try {
      const res = await fetch("http://localhost:8000/send-email", {
        method: "POST",
        body: formData
      });
      
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to send email");
      }

      setMessage("Email sent successfully!");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ padding: "40px", maxWidth: "800px", margin: "auto"}}>
      <h2>Job Application Email Generator</h2>
      
      <textarea
        placeholder = "Paste Job Description here..."
        value = {jdText}
        onChange = {(e) => setJdText(e.target.value)}
        rows = {6}
        style = {{ width: "100%"}}
      />

      <br /><br />

      <input
        type = "file"
        accept = "application/pdf"
        onChange={(e) => setResumeFile(e.target.files[0])}
      />

      <br /><br />

      <button onClick={handleGenerate} disabled={generating}>
        {generating ? "Generating..." : "Generate Email"}
      </button>
      <hr/>

      <input
        placeholder="Recipient"
        value={recipient}
        onChange={(e) => setRecipient(e.target.value)}
        style={{ width: "100%"}}
      />

      <br /><br />

      <input
        placeholder="Subject"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
        style={{ width: "100%"}}
      />

      <br /><br />

      <textarea
        placeholder = "Email Body"
        value = {body}
        onChange = {(e) => setBody(e.target.value)}
        rows = {8}
        style = {{ width: "100%"}}
      />

      <br /><br />

      <button onClick={handleSend} disabled={sending}>
        {sending ? "Sending..." : "Send Email"}
      </button>

      {message && <p>{message}</p>}
    </div>
  );
}

export default App
