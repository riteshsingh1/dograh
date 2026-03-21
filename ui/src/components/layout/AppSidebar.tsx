"use client";

import type { Team } from "@stackframe/stack";
import {
  Brain,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Database,
  FileText,
  Home,
  Key,
  LogOut,
  Megaphone,
  Phone,
  Settings,
  Star,
  TrendingUp,
  Workflow,
  Wrench,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import React, { useRef } from "react";

import ThemeToggle from "@/components/ThemeSwitcher";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAppConfig } from "@/context/AppConfigContext";
import type { LocalUser } from "@/lib/auth";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

// Lazy load SelectedTeamSwitcher - we'll pass selectedTeam from our context
const StackTeamSwitcher = React.lazy(() =>
  import("@stackframe/stack").then((mod) => ({
    default: mod.SelectedTeamSwitcher,
  }))
);

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { state, isMobile, setOpenMobile } = useSidebar();
  const { provider, getSelectedTeam, logout, user } = useAuth();
  const { config } = useAppConfig();

  // Get selected team for Stack auth (cast to Team type from Stack)
  // Stabilize the reference so SelectedTeamSwitcher only sees a change when the team ID changes,
  // preventing unnecessary PATCH calls to Stack Auth on every route navigation.
  const selectedTeamRef = useRef<Team | null>(null);
  const rawSelectedTeam = provider === "stack" && getSelectedTeam ? getSelectedTeam() as Team | null : null;
  if (rawSelectedTeam?.id !== selectedTeamRef.current?.id) {
    selectedTeamRef.current = rawSelectedTeam;
  }
  const selectedTeam = selectedTeamRef.current;

  // Version info from app config context
  const versionInfo = config ? { ui: config.uiVersion, api: config.apiVersion } : null;

  const isActive = (path: string) => {
    return pathname.startsWith(path);
  };


  // Organize navigation into sections
  const overviewSection = [
    {
      title: "Overview",
      url: "/overview",
      icon: Home,
    },
  ];

  const buildSection = [
        {
          title: "Voice Agents",
          url: "/workflow",
          icon: Workflow,
        },
        {
          title: "Campaigns",
          url: "/campaigns",
          icon: Megaphone,
        },
        // {
        //   title: "Automation",
        //   url: "/automation",
        //   icon: Zap,
        // },
        {
          title: "Models",
          url: "/model-configurations",
          icon: Brain,
        },
        {
          title: "Telephony",
          url: "/telephony-configurations",
          icon: Phone,
        },
        {
          title: "Tools",
          url: "/tools",
          icon: Wrench,
        },
        {
          title: "Files",
          url: "/files",
          icon: Database,
        },
        // {
        //   title: "Integrations",
        //   url: "/integrations",
        //   icon: Plug,
        // },
        // {
        //   title: "Developers",
        //   url: "/api-keys",
        //   icon: Key,
        // },
      ];

  const observeSection = [
    {
      title: "Usage",
      url: "/usage",
      icon: TrendingUp,
    },
    {
      title: "Reports",
      url: "/reports",
      icon: FileText,
    },
    // {
    //   title: "LoopTalk",
    //   url: "/looptalk",
    //   icon: MessageSquare,
    // },
  ];

  const handleMobileNavClick = () => {
    if (isMobile) {
      setOpenMobile(false);
    }
  };

  const SidebarLink = ({ item }: { item: typeof overviewSection[0] }) => {
    const isItemActive = isActive(item.url);
    const Icon = item.icon;

    const linkClasses = cn(
      "transition-all duration-150",
      "hover:bg-accent hover:text-accent-foreground",
      isItemActive && "bg-primary/10 text-primary font-medium border-primary/20"
    );

    if (state === "collapsed") {
      return (
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger asChild>
              <SidebarMenuButton
                asChild
                className={linkClasses}
              >
                <Link href={item.url} onClick={handleMobileNavClick}>
                  <Icon className={cn("h-4 w-4", isItemActive && "text-primary")} />
                  <span className="sr-only">{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>{item.title}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return (
      <SidebarMenuButton
        asChild
        className={linkClasses}
      >
        <Link href={item.url} onClick={handleMobileNavClick}>
          <Icon className={cn("h-4 w-4", isItemActive && "text-primary")} />
          <span>{item.title}</span>
        </Link>
      </SidebarMenuButton>
    );
  };

  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader className="border-b px-2 py-3">
        <div className="flex items-center justify-between">
          {state === "expanded" && (
            <Link
              href="/"
              className="flex items-center gap-2.5 px-2 group"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground text-xs font-bold shadow-sm">
                T
              </div>
              <span className="text-base font-semibold tracking-tight">
                TestOFire
                {versionInfo && (
                  <span className="ml-1.5 text-[10px] font-normal text-muted-foreground align-middle">
                    v{versionInfo.ui}
                  </span>
                )}
              </span>
            </Link>
          )}
          <SidebarTrigger className={cn(
            "hover:bg-accent transition-colors",
            state === "collapsed" && "mx-auto"
          )}>
            {state === "expanded" ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </SidebarTrigger>
        </div>

        {/* Team Switcher for Stack Auth - at the top */}
        {provider === "stack" && state === "expanded" && (
          <div className="mt-3">
            <React.Suspense
              fallback={
                <div className="h-9 w-full animate-pulse bg-muted rounded" />
              }
            >
              <StackTeamSwitcher
                selectedTeam={selectedTeam || undefined}
                onChange={() => {
                  router.refresh();
                }}
              />
            </React.Suspense>
          </div>
        )}

        {/* Star us on GitHub for OSS mode - at the top */}
        {provider !== "stack" && (
          <div className="mt-3 px-2">
            {state === "collapsed" ? (
              <TooltipProvider delayDuration={0}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="w-full hover:bg-accent hover:text-accent-foreground"
                      asChild
                    >
                      <a
                        href="mailto:support@testofire.com"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="sr-only">Send feedback</span>
                      </a>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>Send feedback</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <Button
                variant="ghost"
                className="w-full justify-start hover:bg-accent hover:text-accent-foreground"
                asChild
              >
                <a
                  href="mailto:support@testofire.com"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  <span className="ml-2">Send feedback</span>
                </a>
              </Button>
            )}
          </div>
        )}
      </SidebarHeader>

      <SidebarContent className={cn(
        state === "collapsed" && "px-0"
      )}>
        {/* Overview Section */}
        <SidebarGroup className="mt-2">
          <SidebarMenu>
            {overviewSection.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarLink item={item} />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>

        {/* BUILD Section */}
        {buildSection.length > 0 && (
          <SidebarGroup className="mt-6">
            {state === "expanded" && (
              <SidebarGroupLabel className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                BUILD
              </SidebarGroupLabel>
            )}
            <SidebarMenu>
              {buildSection.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarLink item={item} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        )}

        {/* OBSERVE Section */}
        <SidebarGroup className="mt-6">
          {state === "expanded" && (
            <SidebarGroupLabel className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              OBSERVE
            </SidebarGroupLabel>
          )}
          <SidebarMenu>
            {observeSection.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarLink item={item} />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className={cn(
        "border-t p-4",
        state === "collapsed" && "p-2"
      )}>
        {/* Bottom Actions */}
        <div className="space-y-2">
          {/* User Button - for local/OSS mode */}
          {provider !== "stack" && (
            <div className={cn(
              "flex",
              state === "collapsed" ? "justify-center" : "justify-start"
            )}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 cursor-pointer bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary">
                    <span className="text-xs font-semibold">
                      {(user?.displayName || (user as LocalUser | undefined)?.email || "")
                        .split(/[\s@]/)
                        .filter(Boolean)
                        .slice(0, 2)
                        .map((s: string) => s[0]?.toUpperCase())
                        .join("")
                        || "U"}
                    </span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="top" align="start" className="w-56">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      {(user as LocalUser | undefined)?.email && (
                        <p className="text-xs text-muted-foreground">{(user as LocalUser).email}</p>
                      )}
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => logout()} className="cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

          {/* User Button - for Stack auth */}
          {provider === "stack" && (
            <div className={cn(
              "flex",
              state === "collapsed" ? "justify-center" : "justify-start"
            )}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 cursor-pointer bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary">
                    <span className="text-xs font-semibold">
                      {(user?.displayName || (user as { primaryEmail?: string })?.primaryEmail || "")
                        .split(/[\s@]/)
                        .filter(Boolean)
                        .slice(0, 2)
                        .map((s: string) => s[0]?.toUpperCase())
                        .join("")
                        || "U"}
                    </span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="top" align="start" className="w-56">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      {user?.displayName && (
                        <p className="text-sm font-medium">{user.displayName}</p>
                      )}
                      {(user as { primaryEmail?: string })?.primaryEmail && (
                        <p className="text-xs text-muted-foreground">{(user as { primaryEmail?: string }).primaryEmail}</p>
                      )}
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => router.push("/handler/account-settings")} className="cursor-pointer">
                    <Settings className="mr-2 h-4 w-4" />
                    Account settings
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => router.push("/usage")} className="cursor-pointer">
                    <CircleDollarSign className="mr-2 h-4 w-4" />
                    Usage
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => logout()} className="cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

          {/* Theme Toggle - at the very bottom */}
          <div className={cn(
            "mt-2 pt-2 border-t",
            state === "collapsed" ? "flex justify-center" : ""
          )}>
            {state === "collapsed" ? (
              <TooltipProvider delayDuration={0}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div>
                      <ThemeToggle
                        showLabel={false}
                        className="hover:bg-accent hover:text-accent-foreground"
                      />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>Toggle theme</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <ThemeToggle
                showLabel={true}
                className="hover:bg-accent hover:text-accent-foreground"
              />
            )}
          </div>

        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
