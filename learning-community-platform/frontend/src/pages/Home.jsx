import { Link } from 'react-router-dom';
import { AcademicCapIcon, UserGroupIcon, TrophyIcon, SparklesIcon, BeakerIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import GoogleAdPlaceholder from '../components/GoogleAdPlaceholder';

const Home = () => {
  const features = [
    {
      icon: UserGroupIcon,
      title: 'Community Learning',
      description: 'Connect with learners at all skill levels in an interactive Discord-like environment',
    },
    {
      icon: AcademicCapIcon,
      title: 'Curated Subjects',
      description: 'Browse through a vast library of topics and find your next learning adventure',
    },
    {
      icon: TrophyIcon,
      title: 'Gamified Experience',
      description: 'Earn karma points, badges, and rewards as you learn and contribute to the community',
    },
    {
      icon: BeakerIcon,
      title: 'Research Platform',
      description: 'Publish your research, find collaborators, and contribute to knowledge',
    },
    {
      icon: ChatBubbleLeftRightIcon,
      title: 'Real-time Messaging',
      description: 'Chat with fellow learners, join study groups, and collaborate on projects',
    },
    {
      icon: SparklesIcon,
      title: 'AI & Human Learning',
      description: 'Clearly labeled AI-assisted content alongside human expertise',
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-8 py-12">
        <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
          Welcome to SkillSphere
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
          Your Community Learning Hub - Where Knowledge Grows Together
        </p>
        <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
          Join thousands of learners exploring topics, mastering skills, and building meaningful connections
          in an interactive, gamified learning environment.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link to="/register" className="btn-primary text-lg px-8 py-3">
            Get Started Free
          </Link>
          <Link to="/topics" className="btn-secondary text-lg px-8 py-3">
            Explore Topics
          </Link>
        </div>
      </section>

      {/* Google Ad */}
      <GoogleAdPlaceholder slot="homepage-top" />

      {/* Features Grid */}
      <section className="space-y-8">
        <h2 className="text-3xl font-bold text-center">Why Choose SkillSphere?</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card hover:shadow-xl transition-shadow">
              <feature.icon className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="space-y-8 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-8 md:p-12">
        <h2 className="text-3xl font-bold text-center">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="text-center space-y-3">
            <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto">
              1
            </div>
            <h3 className="font-semibold text-lg">Sign Up</h3>
            <p className="text-gray-600 dark:text-gray-300">Create your free account in seconds</p>
          </div>
          <div className="text-center space-y-3">
            <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto">
              2
            </div>
            <h3 className="font-semibold text-lg">Choose Topics</h3>
            <p className="text-gray-600 dark:text-gray-300">Select topics you want to learn about</p>
          </div>
          <div className="text-center space-y-3">
            <div className="w-16 h-16 bg-pink-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto">
              3
            </div>
            <h3 className="font-semibold text-lg">Learn & Connect</h3>
            <p className="text-gray-600 dark:text-gray-300">Engage with lessons and community</p>
          </div>
          <div className="text-center space-y-3">
            <div className="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto">
              4
            </div>
            <h3 className="font-semibold text-lg">Earn Rewards</h3>
            <p className="text-gray-600 dark:text-gray-300">Gain karma, badges, and points</p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="grid md:grid-cols-3 gap-8 text-center">
        <div className="card">
          <div className="text-4xl font-bold text-primary-600">10,000+</div>
          <div className="text-gray-600 dark:text-gray-400 mt-2">Active Learners</div>
        </div>
        <div className="card">
          <div className="text-4xl font-bold text-purple-600">500+</div>
          <div className="text-gray-600 dark:text-gray-400 mt-2">Expert Teachers</div>
        </div>
        <div className="card">
          <div className="text-4xl font-bold text-pink-600">1,000+</div>
          <div className="text-gray-600 dark:text-gray-400 mt-2">Courses Available</div>
        </div>
      </section>

      {/* Google Ad */}
      <GoogleAdPlaceholder slot="homepage-bottom" />

      {/* CTA Section */}
      <section className="text-center space-y-6 py-12 bg-gradient-to-r from-primary-600 to-purple-600 rounded-2xl text-white">
        <h2 className="text-3xl md:text-4xl font-bold">Ready to Start Your Learning Journey?</h2>
        <p className="text-lg md:text-xl opacity-90 max-w-2xl mx-auto">
          Join our community today and unlock endless learning possibilities
        </p>
        <Link to="/register" className="inline-block px-8 py-3 bg-white text-primary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors">
          Join SkillSphere Now
        </Link>
      </section>
    </div>
  );
};

export default Home;
