import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
    AmbientNoiseConfiguration,
    CampaignIntegrationsConfiguration,
    TurnStopStrategy,
    WorkflowConfigurations
} from "@/types/workflow-configurations";

interface ConfigurationsDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    workflowConfigurations: WorkflowConfigurations | null;
    workflowName: string;
    onSave: (configurations: WorkflowConfigurations, workflowName: string) => Promise<void>;
}

const DEFAULT_AMBIENT_NOISE_CONFIG: AmbientNoiseConfiguration = {
    enabled: false,
    volume: 0.3,
};

const DEFAULT_CAMPAIGN_CONFIG: CampaignIntegrationsConfiguration = {
    mode: 'google-sheet',
    meta_ads: {
        access_token: '',
        lead_form_id: '',
    },
    google_sheets: {
        input_sheet_url: '',
        output_sheet_url: '',
        access_token: '',
    },
    pricing: {
        credit_limit_inr: undefined,
    },
};

export const ConfigurationsDialog = ({
    open,
    onOpenChange,
    workflowConfigurations,
    workflowName,
    onSave
}: ConfigurationsDialogProps) => {
    const [name, setName] = useState<string>(workflowName);
    const [ambientNoiseConfig, setAmbientNoiseConfig] = useState<AmbientNoiseConfiguration>(
        workflowConfigurations?.ambient_noise_configuration || DEFAULT_AMBIENT_NOISE_CONFIG
    );
    const [maxCallDuration, setMaxCallDuration] = useState<number>(
        workflowConfigurations?.max_call_duration || 600  // Default 10 minutes
    );
    const [maxUserIdleTimeout, setMaxUserIdleTimeout] = useState<number>(
        workflowConfigurations?.max_user_idle_timeout || 10  // Default 10 seconds
    );
    const [smartTurnStopSecs, setSmartTurnStopSecs] = useState<number>(
        workflowConfigurations?.smart_turn_stop_secs || 2  // Default 2 seconds
    );
    const [turnStopStrategy, setTurnStopStrategy] = useState<TurnStopStrategy>(
        workflowConfigurations?.turn_stop_strategy || 'transcription'
    );
    const [campaignConfig, setCampaignConfig] = useState<CampaignIntegrationsConfiguration>(
        workflowConfigurations?.campaign_integrations || DEFAULT_CAMPAIGN_CONFIG
    );
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await onSave({
                ambient_noise_configuration: ambientNoiseConfig,
                max_call_duration: maxCallDuration,
                max_user_idle_timeout: maxUserIdleTimeout,
                smart_turn_stop_secs: smartTurnStopSecs,
                turn_stop_strategy: turnStopStrategy,
                campaign_integrations: campaignConfig,
            }, name);
            onOpenChange(false);
        } catch (error) {
            console.error("Failed to save configurations:", error);
        } finally {
            setIsSaving(false);
        }
    };

    // Sync state with props when dialog opens
    useEffect(() => {
        if (open) {
            setName(workflowName);
            setAmbientNoiseConfig(workflowConfigurations?.ambient_noise_configuration || DEFAULT_AMBIENT_NOISE_CONFIG);
            setMaxCallDuration(workflowConfigurations?.max_call_duration || 600);
            setMaxUserIdleTimeout(workflowConfigurations?.max_user_idle_timeout || 10);
            setSmartTurnStopSecs(workflowConfigurations?.smart_turn_stop_secs || 2);
            setTurnStopStrategy(workflowConfigurations?.turn_stop_strategy || 'transcription');
            setCampaignConfig(workflowConfigurations?.campaign_integrations || DEFAULT_CAMPAIGN_CONFIG);
        }
    }, [open, workflowName, workflowConfigurations]);

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>Configurations</DialogTitle>
                </DialogHeader>

                <div className="space-y-6">
                    {/* Workflow Name Section */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-semibold mb-1">Agent Name</h3>
                            <p className="text-xs text-muted-foreground">
                                The name of your agent
                            </p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="workflow_name" className="text-xs">
                                Name
                            </Label>
                            <Input
                                id="workflow_name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter Agent name"
                            />
                        </div>
                    </div>

                    {/* Ambient Noise Section */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-semibold mb-1">Ambient Noise</h3>
                            <p className="text-xs text-muted-foreground">
                                Add background office ambient noise to make the conversation sound more natural.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="ambient-noise-enabled" className="text-sm">
                                    Use Ambient Noise
                                </Label>
                                <Switch
                                    id="ambient-noise-enabled"
                                    checked={ambientNoiseConfig.enabled}
                                    onCheckedChange={(checked) =>
                                        setAmbientNoiseConfig(prev => ({ ...prev, enabled: checked }))
                                    }
                                />
                            </div>

                            {ambientNoiseConfig.enabled && (
                                <div className="space-y-2">
                                    <Label htmlFor="ambient-volume" className="text-xs">
                                        Volume
                                    </Label>
                                    <Input
                                        id="ambient-volume"
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        max="1"
                                        value={ambientNoiseConfig.volume}
                                        onChange={(e) => {
                                            const value = parseFloat(e.target.value);
                                            if (!isNaN(value)) {
                                                setAmbientNoiseConfig(prev => ({ ...prev, volume: value }));
                                            }
                                        }}
                                    />
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Turn Detection Section */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-semibold mb-1">Turn Detection</h3>
                            <p className="text-xs text-muted-foreground">
                                Configure how the agent detects when the user has finished speaking.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="turn_stop_strategy" className="text-xs">
                                Detection Strategy
                            </Label>
                            <Select
                                value={turnStopStrategy}
                                onValueChange={(value: TurnStopStrategy) => setTurnStopStrategy(value)}
                            >
                                <SelectTrigger id="turn_stop_strategy">
                                    <SelectValue placeholder="Select strategy" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="transcription">
                                        Transcription-based
                                    </SelectItem>
                                    <SelectItem value="turn_analyzer">
                                        Smart Turn Analyzer
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-muted-foreground">
                                {turnStopStrategy === 'transcription'
                                    ? "Best for short responses (1-2 word statements). Ends turn when transcription indicates completion."
                                    : "Best for longer responses with natural pauses. Uses ML model to detect end of turn."}
                            </p>
                        </div>

                        {turnStopStrategy === 'turn_analyzer' && (
                            <div className="space-y-2">
                                <Label htmlFor="smart_turn_stop_secs" className="text-xs">
                                    Incomplete Turn Timeout (seconds)
                                </Label>
                                <Input
                                    id="smart_turn_stop_secs"
                                    type="number"
                                    step="0.5"
                                    min="0.5"
                                    max="10"
                                    value={smartTurnStopSecs}
                                    onChange={(e) => {
                                        const value = parseFloat(e.target.value);
                                        if (!isNaN(value) && value >= 0.5) {
                                            setSmartTurnStopSecs(value);
                                        }
                                    }}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Max silence duration before ending an incomplete turn. Default: 2 seconds
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Call Management Section */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-semibold mb-1">Call Management</h3>
                            <p className="text-xs text-muted-foreground">
                                Configure call duration limits and idle timeout settings.
                            </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_call_duration" className="text-xs">
                                    Max Call Duration (seconds)
                                </Label>
                                <Input
                                    id="max_call_duration"
                                    type="number"
                                    step="1"
                                    min="1"
                                    value={maxCallDuration}
                                    onChange={(e) => {
                                        const value = parseInt(e.target.value);
                                        if (!isNaN(value) && value > 0) {
                                            setMaxCallDuration(value);
                                        }
                                    }}
                                />
                                <p className="text-xs text-muted-foreground">Default: 600 (10 minutes)</p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="max_user_idle_timeout" className="text-xs">
                                    Max User Idle Timeout (seconds)
                                </Label>
                                <Input
                                    id="max_user_idle_timeout"
                                    type="number"
                                    step="1"
                                    min="1"
                                    value={maxUserIdleTimeout}
                                    onChange={(e) => {
                                        const value = parseInt(e.target.value);
                                        if (!isNaN(value) && value > 0) {
                                            setMaxUserIdleTimeout(value);
                                        }
                                    }}
                                />
                                <p className="text-xs text-muted-foreground">Default: 10 seconds</p>
                            </div>
                        </div>
                    </div>

                    {/* Campaign Integrations Section */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-semibold mb-1">Campaign Integrations</h3>
                            <p className="text-xs text-muted-foreground">
                                Configure workflow-level source credentials, output sheet, and INR credit limit.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="campaign_mode" className="text-xs">Campaign Mode</Label>
                            <Select
                                value={campaignConfig.mode || 'google-sheet'}
                                onValueChange={(value: 'meta-ads' | 'google-sheet') =>
                                    setCampaignConfig(prev => ({ ...prev, mode: value }))
                                }
                            >
                                <SelectTrigger id="campaign_mode">
                                    <SelectValue placeholder="Select campaign mode" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="google-sheet">Google Sheets input + output</SelectItem>
                                    <SelectItem value="meta-ads">Meta Ads input + Google Sheets output</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="meta_access_token" className="text-xs">Meta Access Token</Label>
                                <Input
                                    id="meta_access_token"
                                    type="password"
                                    value={campaignConfig.meta_ads?.access_token || ''}
                                    onChange={(e) => setCampaignConfig(prev => ({
                                        ...prev,
                                        meta_ads: {
                                            ...(prev.meta_ads || {}),
                                            access_token: e.target.value,
                                        },
                                    }))}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="meta_lead_form_id" className="text-xs">Meta Lead Form ID</Label>
                                <Input
                                    id="meta_lead_form_id"
                                    type="text"
                                    value={campaignConfig.meta_ads?.lead_form_id || ''}
                                    onChange={(e) => setCampaignConfig(prev => ({
                                        ...prev,
                                        meta_ads: {
                                            ...(prev.meta_ads || {}),
                                            lead_form_id: e.target.value,
                                        },
                                    }))}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="gs_input_sheet_url" className="text-xs">Google Input Sheet URL</Label>
                                <Input
                                    id="gs_input_sheet_url"
                                    type="text"
                                    value={campaignConfig.google_sheets?.input_sheet_url || ''}
                                    onChange={(e) => setCampaignConfig(prev => ({
                                        ...prev,
                                        google_sheets: {
                                            ...(prev.google_sheets || {}),
                                            input_sheet_url: e.target.value,
                                        },
                                    }))}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="gs_output_sheet_url" className="text-xs">Google Output Sheet URL</Label>
                                <Input
                                    id="gs_output_sheet_url"
                                    type="text"
                                    value={campaignConfig.google_sheets?.output_sheet_url || ''}
                                    onChange={(e) => setCampaignConfig(prev => ({
                                        ...prev,
                                        google_sheets: {
                                            ...(prev.google_sheets || {}),
                                            output_sheet_url: e.target.value,
                                        },
                                    }))}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="gs_access_token" className="text-xs">Google Access Token (optional override)</Label>
                                <Input
                                    id="gs_access_token"
                                    type="password"
                                    value={campaignConfig.google_sheets?.access_token || ''}
                                    onChange={(e) => setCampaignConfig(prev => ({
                                        ...prev,
                                        google_sheets: {
                                            ...(prev.google_sheets || {}),
                                            access_token: e.target.value,
                                        },
                                    }))}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="credit_limit_inr" className="text-xs">Workflow Credit Limit (INR)</Label>
                                <Input
                                    id="credit_limit_inr"
                                    type="number"
                                    min="0"
                                    step="1"
                                    value={campaignConfig.pricing?.credit_limit_inr ?? ''}
                                    onChange={(e) => {
                                        const parsed = e.target.value === '' ? undefined : Number(e.target.value);
                                        setCampaignConfig(prev => ({
                                            ...prev,
                                            pricing: {
                                                ...(prev.pricing || {}),
                                                credit_limit_inr: Number.isFinite(parsed) ? parsed : undefined,
                                            },
                                        }));
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? "Saving..." : "Save"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

