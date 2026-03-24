"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface GoogleSheetSelectorProps {
  selectedSheetUrl: string;
  outputSheetUrl: string;
  authType: "access_token" | "oauth_refresh_token";
  googleAccessToken: string;
  refreshToken: string;
  clientId: string;
  clientSecret: string;
  onSheetUrlChange: (value: string) => void;
  onOutputSheetUrlChange: (value: string) => void;
  onAuthTypeChange: (value: "access_token" | "oauth_refresh_token") => void;
  onGoogleAccessTokenChange: (value: string) => void;
  onRefreshTokenChange: (value: string) => void;
  onClientIdChange: (value: string) => void;
  onClientSecretChange: (value: string) => void;
}

export default function GoogleSheetSelector({
  selectedSheetUrl,
  outputSheetUrl,
  authType,
  googleAccessToken,
  refreshToken,
  clientId,
  clientSecret,
  onSheetUrlChange,
  onOutputSheetUrlChange,
  onAuthTypeChange,
  onGoogleAccessTokenChange,
  onRefreshTokenChange,
  onClientIdChange,
  onClientSecretChange,
}: GoogleSheetSelectorProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="google-auth-type">Google Auth Type</Label>
        <Select
          value={authType}
          onValueChange={(value) =>
            onAuthTypeChange(value as "access_token" | "oauth_refresh_token")
          }
        >
          <SelectTrigger id="google-auth-type">
            <SelectValue placeholder="Select auth type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="access_token">Access Token</SelectItem>
            <SelectItem value="oauth_refresh_token">Refresh Token (recommended)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="google-input-sheet-url">Google Input Sheet URL</Label>
        <Input
          id="google-input-sheet-url"
          placeholder="https://docs.google.com/spreadsheets/d/..."
          value={selectedSheetUrl}
          onChange={(e) => onSheetUrlChange(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="google-output-sheet-url">Google Output Sheet URL (optional)</Label>
        <Input
          id="google-output-sheet-url"
          placeholder="https://docs.google.com/spreadsheets/d/..."
          value={outputSheetUrl}
          onChange={(e) => onOutputSheetUrlChange(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        {authType === "access_token" ? (
          <>
            <Label htmlFor="google-access-token">Google Access Token</Label>
            <Input
              id="google-access-token"
              type="password"
              placeholder="Paste token for this campaign"
              value={googleAccessToken}
              onChange={(e) => onGoogleAccessTokenChange(e.target.value)}
              required
            />
          </>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-2">
              <Label htmlFor="google-refresh-token">Google Refresh Token</Label>
              <Input
                id="google-refresh-token"
                type="password"
                placeholder="Paste refresh token"
                value={refreshToken}
                onChange={(e) => onRefreshTokenChange(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="google-client-id">Google OAuth Client ID</Label>
              <Input
                id="google-client-id"
                placeholder="Paste OAuth client id"
                value={clientId}
                onChange={(e) => onClientIdChange(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="google-client-secret">Google OAuth Client Secret</Label>
              <Input
                id="google-client-secret"
                type="password"
                placeholder="Paste OAuth client secret"
                value={clientSecret}
                onChange={(e) => onClientSecretChange(e.target.value)}
                required
              />
            </div>
          </div>
        )}
      </div>

      <p className="text-sm text-muted-foreground">
        This campaign will use the token and sheet details entered above. No integration setup is required.
      </p>
    </div>
  );
}
