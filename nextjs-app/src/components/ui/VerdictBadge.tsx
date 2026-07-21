import { Verdict } from "@/types";
import { CheckCircle, XCircle, Clock, AlertTriangle, HelpCircle, Code as CodeIcon } from "lucide-react";

interface VerdictBadgeProps {
  verdict: Verdict;
  showIcon?: boolean;
}

export function VerdictBadge({ verdict, showIcon = true }: VerdictBadgeProps) {
  const config = {
    AC: { label: "Accepted", color: "text-green-500 bg-green-500/10 border border-green-500/20", icon: CheckCircle },
    WA: { label: "Wrong Answer", color: "text-red-500 bg-red-500/10 border border-red-500/20", icon: XCircle },
    TLE: { label: "Time Limit Exceeded", color: "text-yellow-500 bg-yellow-500/10 border border-yellow-500/20", icon: Clock },
    RE: { label: "Runtime Error", color: "text-orange-500 bg-orange-500/10 border border-orange-500/20", icon: AlertTriangle },
    CE: { label: "Compilation Error", color: "text-gray-500 bg-gray-500/10 border border-gray-500/20", icon: CodeIcon },
    PE: { label: "Pending", color: "text-blue-500 bg-blue-500/10 border border-blue-500/20", icon: Clock },
    IE: { label: "Internal Error", color: "text-purple-500 bg-purple-500/10 border border-purple-500/20", icon: HelpCircle },
  };

  const { label, color, icon: Icon } = config[verdict] || config.IE;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${color}`}>
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      {label}
    </span>
  );
}
