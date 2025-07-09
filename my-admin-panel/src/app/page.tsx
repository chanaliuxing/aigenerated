'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import { 
  ChatBubbleLeftRightIcon, 
  UsersIcon, 
  Cog6ToothIcon,
  ChartBarIcon,
  KeyIcon,
  DocumentTextIcon,
  BoltIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

import Layout from '@/components/Layout';
import StatsCard from '@/components/StatsCard';
import RecentActivity from '@/components/RecentActivity';
import QuickActions from '@/components/QuickActions';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';

interface DashboardStats {
  totalConversations: number;
  activeConversations: number;
  totalMessages: number;
  averageResponseTime: number;
  conversionRate: number;
  topPhases: Array<{
    phase: string;
    count: number;
    percentage: number;
  }>;
}

interface RecentActivityItem {
  id: string;
  type: 'message' | 'conversation' | 'phase_change';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
  status?: 'success' | 'warning' | 'error';
}

export default function Dashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await api.get('/api/dashboard/stats');
      setStats(statsResponse.data);
      
      // Fetch recent activity
      const activityResponse = await api.get('/api/dashboard/activity');
      setRecentActivity(activityResponse.data);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      name: 'View Conversations',
      description: 'Monitor active conversations',
      icon: ChatBubbleLeftRightIcon,
      action: () => router.push('/conversations'),
      color: 'bg-blue-500'
    },
    {
      name: 'Manage Prompts',
      description: 'Edit AI prompt templates',
      icon: DocumentTextIcon,
      action: () => router.push('/prompts'),
      color: 'bg-green-500'
    },
    {
      name: 'API Keys',
      description: 'Manage AI provider keys',
      icon: KeyIcon,
      action: () => router.push('/settings/api-keys'),
      color: 'bg-purple-500'
    },
    {
      name: 'Workflows',
      description: 'Configure automation workflows',
      icon: BoltIcon,
      action: () => router.push('/workflows'),
      color: 'bg-orange-500'
    },
  ];

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Dashboard
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Welcome back, {user?.username}! Here's what's happening with your legal chatbot.
            </p>
          </div>
          <div className="mt-4 flex md:mt-0 md:ml-4">
            <button
              onClick={fetchDashboardData}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Total Conversations"
              value={stats.totalConversations}
              icon={ChatBubbleLeftRightIcon}
              color="blue"
              trend={stats.totalConversations > 0 ? 'up' : 'neutral'}
            />
            <StatsCard
              title="Active Conversations"
              value={stats.activeConversations}
              icon={UsersIcon}
              color="green"
              trend={stats.activeConversations > 0 ? 'up' : 'neutral'}
            />
            <StatsCard
              title="Total Messages"
              value={stats.totalMessages}
              icon={DocumentTextIcon}
              color="purple"
              trend={stats.totalMessages > 0 ? 'up' : 'neutral'}
            />
            <StatsCard
              title="Avg Response Time"
              value={`${stats.averageResponseTime}s`}
              icon={ChartBarIcon}
              color="orange"
              trend={stats.averageResponseTime < 5 ? 'up' : 'down'}
            />
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Recent Activity
              </h3>
              <RecentActivity activities={recentActivity} />
              <div className="mt-4">
                <button
                  onClick={() => router.push('/activity')}
                  className="text-sm text-blue-600 hover:text-blue-500 font-medium inline-flex items-center"
                >
                  View all activity
                  <ArrowRightIcon className="ml-1 h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Quick Actions
              </h3>
              <QuickActions actions={quickActions} />
            </div>
          </div>
        </div>

        {/* Phase Distribution */}
        {stats && stats.topPhases.length > 0 && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Conversation Phases
              </h3>
              <div className="space-y-3">
                {stats.topPhases.map((phase, index) => (
                  <div key={index} className="flex items-center">
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">
                          {phase.phase.replace(/_/g, ' ')}
                        </span>
                        <span className="text-sm text-gray-500">
                          {phase.count} ({phase.percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${phase.percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
