import { useState, lazy, Suspense } from 'react';
const ReactQuill = lazy(() => import('react-quill-new'));
import 'react-quill-new/dist/quill.snow.css';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, FileText, Sparkles, Loader2, Mail, Briefcase, X, RefreshCw } from 'lucide-react';

function App() {
  const [jdText, setJdText] = useState("We are hiring for Junior AI/ML developer at example.com. We need people with 1 year of experience. Interested candidates mail at hr@example..com or hra@example.com and keep ceo@example.com in cc");
  const [resumeFile, setResumeFile] = useState(null);

  const [recipient, setRecipient] = useState("");
  const [cc, setCc] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("success");

  const handleGenerate = async () => {
    if (!jdText) {
      showMessage("Please enter Job Description", "error");
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
      const res = await fetch("http://localhost:5000/generate-email", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to generate email");
      }

      setRecipient(data.data.recipient || "");
      setCc(data.data.cc || "");
      setSubject(data.data.subject || "");
      setBody(data.data.body || "");
      setHasGenerated(true);

      showMessage("Email generated successfully!", "success");
    } catch (error) {
      showMessage(error.message, "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleSend = async () => {
    if (!recipient || !subject || !body) {
      showMessage("Recipient, Subject and Body are required to send email", "error");
      return;
    }

    setSending(true);
    setMessage("");

    // Process body to remove extra paragraph spacing from ReactQuill
    // Convert <p>...</p> to content with <br> for line breaks
    let processedBody = body
      .replace(/<p>/gi, '')           // Remove opening <p> tags
      .replace(/<\/p>/gi, '<br><br>') // Replace closing </p> with double <br> for paragraph spacing
      .replace(/(<br>\s*){3,}/gi, '<br><br>'); // Remove excessive (3+) consecutive <br> tags, keep max 2

    const formData = new FormData();
    formData.append("recipient", recipient);
    formData.append("cc", cc);
    formData.append("subject", subject);
    formData.append("body", processedBody);
    if (resumeFile) {
      formData.append("resume_file", resumeFile);
    }

    try {
      const res = await fetch("http://localhost:5000/send-email", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to send email");
      }

      showMessage("Email sent successfully!", "success");
    } catch (error) {
      showMessage(error.message, "error");
    } finally {
      setSending(false);
    }
  };

  const handleRegenerate = async () => {
    if (!body) {
      showMessage("Please generate an email first before regenerating", "error");
      return;
    }

    const instruction = prompt("Enter instructions to regenerate the email body (or leave empty for default improvement):");

    // If user clicks cancel, don't proceed
    if (instruction === null) {
      return;
    }

    setRegenerating(true);
    setMessage("");

    const formData = new FormData();
    formData.append("original_body", body);
    if (instruction && instruction.trim()) {
      formData.append("instruction", instruction);
    }
    if (resumeFile) {
      formData.append("resume_file", resumeFile);
    }

    try {
      const res = await fetch("http://localhost:5000/regenerate-body", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to regenerate email body");
      }

      setBody(data.body || "");
      showMessage("Email body regenerated successfully!", "success");
    } catch (error) {
      showMessage(error.message, "error");
    } finally {
      setRegenerating(false);
    }
  };

  const showMessage = (msg, type) => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => setMessage(""), 5000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-6 md:p-12">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Left Column: Input Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-8 border border-white/50">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-indigo-100 rounded-lg text-indigo-600">
                <Briefcase size={24} />
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Job Details</h2>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-slate-700">Job Description</label>
                  {jdText && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setJdText("")}
                      className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                      title="Clear job description"
                    >
                      <X size={18} />
                    </motion.button>
                  )}
                </div>
                <textarea
                  placeholder="Paste the job description here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  rows={8}
                  className="w-full rounded-xl border-slate-200 bg-slate-50 focus:border-indigo-500 focus:ring-indigo-500 transition-all resize-none p-4 text-slate-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Resume (PDF)</label>
                <div className="relative group">
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => setResumeFile(e.target.files[0])}
                    className="block w-full text-sm text-slate-500
                      file:mr-4 file:py-2.5 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-indigo-50 file:text-indigo-700
                      hover:file:bg-indigo-100
                      cursor-pointer border border-slate-200 rounded-lg bg-slate-50"
                  />
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleGenerate}
                disabled={generating}
                className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium shadow-lg hover:shadow-indigo-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {generating ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Generating Magic...
                  </>
                ) : (
                  <>
                    <Sparkles size={20} />
                    Generate Email
                  </>
                )}
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Right Column: Email Editor */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="space-y-6"
        >
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-8 border border-white/50 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-purple-100 rounded-lg text-purple-600">
                <Mail size={24} />
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Email Draft</h2>
            </div>

            <div className="space-y-4 flex-1">
              <div className="grid grid-cols-1 gap-4">

                <div className="relative">
                  <span className="absolute left-4 top-3 text-slate-400 text-sm font-medium">To:</span>
                  <input
                    placeholder="recipient@example.com"
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    className="w-full pl-12 pr-4 py-2.5 rounded-lg border-slate-200 bg-slate-50 focus:border-purple-500 focus:ring-purple-500 transition-all"
                  />
                </div>
                <div className="relative">
                  <span className="absolute left-4 top-3 text-slate-400 text-sm font-medium">CC:</span>
                  <input
                    placeholder="cc@example.com"
                    value={cc}
                    onChange={(e) => setCc(e.target.value)}
                    className="w-full pl-12 pr-4 py-2.5 rounded-lg border-slate-200 bg-slate-50 focus:border-purple-500 focus:ring-purple-500 transition-all"
                  />
                </div>
                <div className="relative">
                  <span className="absolute left-4 top-3 text-slate-400 text-sm font-medium">Subject:</span>
                  <input
                    placeholder="Regarding Job Application..."
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full pl-20 pr-4 py-2.5 rounded-lg border-slate-200 bg-slate-50 focus:border-purple-500 focus:ring-purple-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-slate-700">Email Body</label>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleRegenerate}
                    disabled={regenerating || !hasGenerated}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-purple-600 bg-purple-50 rounded-lg hover:bg-purple-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Regenerate email body with custom instructions"
                  >
                    {regenerating ? (
                      <>
                        <Loader2 className="animate-spin" size={16} />
                        Regenerating...
                      </>
                    ) : (
                      <>
                        <RefreshCw size={16} />
                        Regenerate
                      </>
                    )}
                  </motion.button>
                </div>
                <Suspense fallback={<div className="h-64 bg-slate-50 rounded-lg animate-pulse"></div>}>
                  <ReactQuill
                    theme="snow"
                    value={body}
                    onChange={setBody}
                    className="bg-slate-50 rounded-lg"
                    placeholder="Your email content will be generated here..."
                  />
                </Suspense>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSend}
                disabled={sending}
                className="w-full py-3 bg-slate-900 text-white rounded-xl font-medium shadow-lg hover:shadow-slate-900/30 transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed mt-auto"
              >
                {sending ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send size={20} />
                    Send Application
                  </>
                )}
              </motion.button>
            </div>
          </div>
        </motion.div>

      </div >

      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className={`fixed bottom-8 left-1/2 -translate-x-1/2 px-6 py-3 rounded-full shadow-lg border backdrop-blur-md ${messageType === 'error'
              ? 'bg-red-50/90 border-red-200 text-red-600'
              : 'bg-emerald-50/90 border-emerald-200 text-emerald-600'
              }`}
          >
            {message}
          </motion.div>
        )}
      </AnimatePresence>
    </div >
  );
}

export default App;
