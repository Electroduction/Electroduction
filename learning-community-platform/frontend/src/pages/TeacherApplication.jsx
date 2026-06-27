import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

export default function TeacherApplication() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [form, setForm] = useState({ expertise: '', teaching_experience: '', bio: '', lesson_proposal: '', credentials: '' });
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    api.get('/teacher/status').then(r => setStatus(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, [user]);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.expertise || !form.bio || !form.lesson_proposal) {
      toast.error('Please fill in all required fields');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/teacher/apply', form);
      toast.success('Application submitted! We\'ll review it within 3–5 days.');
      setStatus({ status: 'pending' });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit application');
    } finally { setSubmitting(false); }
  };

  if (!user) return (
    <div className="card text-center py-12">
      <div className="text-5xl mb-4">🎓</div>
      <h2 className="text-xl font-bold mb-2">Become a teacher</h2>
      <p className="text-gray-500 mb-4">Sign in to apply</p>
      <button onClick={() => navigate('/login')} className="btn-primary">Sign in</button>
    </div>
  );

  if (loading) return <div className="card text-center py-12 text-gray-400">Loading…</div>;

  if (user.is_teacher || status?.status === 'approved') return (
    <div className="card text-center py-12">
      <div className="text-5xl mb-4">✅</div>
      <h2 className="text-xl font-bold mb-2">You're a verified teacher</h2>
      <p className="text-gray-500 mb-4">Create and publish lessons from your profile or the Lessons page.</p>
      <button onClick={() => navigate('/lessons')} className="btn-primary">View lessons</button>
    </div>
  );

  if (status?.status === 'pending') return (
    <div className="card text-center py-12">
      <div className="text-5xl mb-4">⏳</div>
      <h2 className="text-xl font-bold mb-2">Application under review</h2>
      <p className="text-gray-500">Your teacher application is being reviewed. We'll notify you within 3–5 days.</p>
    </div>
  );

  const KARMA_REQUIRED = 5000;
  const meetsKarma = (user.karma_points || 0) >= KARMA_REQUIRED;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Apply to teach</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Share your knowledge and earn recognition as a verified teacher</p>
      </div>

      {/* Eligibility */}
      <div className="card">
        <h2 className="font-semibold mb-4">Eligibility requirements</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className={`text-xl ${meetsKarma ? 'text-green-600' : 'text-gray-400'}`}>{meetsKarma ? '✅' : '⭕'}</span>
            <div>
              <div className="font-medium">Minimum {KARMA_REQUIRED.toLocaleString()} karma {meetsKarma ? '✓' : `(you have ${(user.karma_points||0).toLocaleString()})`}</div>
              {!meetsKarma && (
                <div className="text-sm text-gray-500">Need {(KARMA_REQUIRED - (user.karma_points||0)).toLocaleString()} more karma — earn it by contributing to the community</div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xl text-green-600">✅</span>
            <div className="font-medium">Verified account</div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xl text-green-600">✅</span>
            <div className="font-medium">Agree to teaching guidelines and content policy</div>
          </div>
        </div>
      </div>

      {/* Benefits */}
      <div className="card">
        <h2 className="font-semibold mb-4">Teacher benefits</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            ['🎓','Verified teacher badge on profile'],
            ['📚','Publish lessons and courses'],
            ['💳','Offer credit-eligible courses (Gold+ rank)'],
            ['📊','Access to student analytics'],
            ['⭐','Earn karma for each student completion'],
            ['🏅','Exclusive teacher rank and rewards'],
          ].map(([icon, text]) => (
            <div key={text} className="flex items-center gap-2 text-sm">
              <span>{icon}</span><span>{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Application form */}
      <div className="card">
        <h2 className="font-semibold mb-4">Application form</h2>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Areas of expertise <span className="text-red-500">*</span></label>
            <input value={form.expertise} onChange={e => setForm({...form, expertise: e.target.value})}
              className="input" placeholder="e.g. Cybersecurity, Machine Learning, Python" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Teaching experience</label>
            <textarea value={form.teaching_experience} onChange={e => setForm({...form, teaching_experience: e.target.value})}
              className="input min-h-[80px]" placeholder="Describe any previous teaching, tutoring, or mentoring experience…" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">About you <span className="text-red-500">*</span></label>
            <textarea value={form.bio} onChange={e => setForm({...form, bio: e.target.value})}
              className="input min-h-[80px]" placeholder="Tell us about your background, projects, and why you want to teach…" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Lesson proposal <span className="text-red-500">*</span></label>
            <textarea value={form.lesson_proposal} onChange={e => setForm({...form, lesson_proposal: e.target.value})}
              className="input min-h-[100px]" placeholder="Describe 1–3 lessons or courses you'd like to create. What will students learn? What level?" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Credentials (optional)</label>
            <textarea value={form.credentials} onChange={e => setForm({...form, credentials: e.target.value})}
              className="input min-h-[60px]" placeholder="Degrees, certifications, publications, GitHub profile, LinkedIn…" />
          </div>
          <button type="submit" disabled={submitting || !meetsKarma} className={`btn-primary w-full ${!meetsKarma ? 'opacity-50 cursor-not-allowed' : ''}`}>
            {submitting ? 'Submitting…' : meetsKarma ? 'Submit application' : `Need ${(KARMA_REQUIRED-(user.karma_points||0)).toLocaleString()} more karma`}
          </button>
        </form>
      </div>
    </div>
  );
}
