"use client";

import { ArrowRight, Bot, Brain, Megaphone, Phone, Wrench } from 'lucide-react';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';

export default function OverviewPage() {
    const { user, provider } = useAuth();
    const isOSSMode = provider !== 'stack';

    const displayName = isOSSMode
        ? null
        : user?.displayName?.split(' ')[0];

    const quickActions = [
        {
            title: "Voice Agents",
            description: "Build and manage conversational AI agents with the visual workflow editor",
            href: "/workflow",
            icon: Bot,
            gradient: "from-primary/10 to-primary/5",
            iconColor: "text-primary",
        },
        {
            title: "Models",
            description: "Configure your LLM, TTS, and STT providers for optimal performance",
            href: "/model-configurations",
            icon: Brain,
            gradient: "from-chart-2/10 to-chart-2/5",
            iconColor: "text-chart-2",
        },
        {
            title: "Campaigns",
            description: "Launch outbound voice campaigns at scale with your agents",
            href: "/campaigns",
            icon: Megaphone,
            gradient: "from-chart-5/10 to-chart-5/5",
            iconColor: "text-chart-5",
        },
        {
            title: "Telephony",
            description: "Connect your phone numbers with Twilio, Vonage, or other providers",
            href: "/telephony-configurations",
            icon: Phone,
            gradient: "from-chart-4/10 to-chart-4/5",
            iconColor: "text-chart-4",
        },
        {
            title: "Tools",
            description: "Create custom function tools your agents can call during conversations",
            href: "/tools",
            icon: Wrench,
            gradient: "from-chart-3/10 to-chart-3/5",
            iconColor: "text-chart-3",
        },
    ];

    return (
        <div className="container mx-auto px-4 py-8 max-w-5xl">
            {/* Hero Section */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background border border-primary/10 p-8 md:p-12 mb-10 animate-fade-in-up">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,var(--brand-muted),transparent_70%)] opacity-50" />
                <div className="relative">
                    <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
                        {isOSSMode ? (
                            "Welcome to TestOFire"
                        ) : (
                            <>Welcome back{displayName ? `, ${displayName}` : ""}</>
                        )}
                    </h1>
                    <p className="mt-3 text-lg text-muted-foreground max-w-2xl">
                        {isOSSMode
                            ? "Your complete platform for building, deploying, and managing AI voice agents."
                            : "Build, deploy, and manage your AI voice agents from one place."
                        }
                    </p>
                    <div className="mt-6 flex flex-wrap gap-3">
                        <Button asChild size="lg">
                            <Link href="/workflow">
                                Get started
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                        </Button>
                        <Button asChild variant="outline" size="lg">
                            <Link href="/workflow/create">
                                Create new agent
                            </Link>
                        </Button>
                    </div>
                </div>
            </div>

            {/* Quick Actions Grid */}
            <div className="mb-4">
                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-5">
                    Quick Actions
                </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {quickActions.map((action, i) => {
                    const Icon = action.icon;
                    return (
                        <Link
                            key={action.href}
                            href={action.href}
                            className={`group relative overflow-hidden rounded-xl border bg-card p-5 transition-all duration-200 hover:shadow-md hover:border-primary/20 hover:-translate-y-0.5 opacity-0 animate-fade-in-up animation-delay-${(i + 1) * 100}`}
                        >
                            <div className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                            <div className="relative">
                                <div className={`inline-flex items-center justify-center rounded-lg bg-gradient-to-br ${action.gradient} p-2.5 mb-3`}>
                                    <Icon className={`h-5 w-5 ${action.iconColor}`} />
                                </div>
                                <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">
                                    {action.title}
                                </h3>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    {action.description}
                                </p>
                            </div>
                            <ArrowRight className="absolute top-5 right-5 h-4 w-4 text-muted-foreground/0 group-hover:text-muted-foreground transition-all duration-200 group-hover:translate-x-0.5" />
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}
