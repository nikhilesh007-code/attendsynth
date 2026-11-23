"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Dataset, AnalyticsScopes, AITestConnectionResponse } from "@/types";
import { api } from "@/lib/api";

interface DatasetContextType {
  activeDataset: Dataset | null;
  datasets: Dataset[];
  scopes: AnalyticsScopes | null;
  loading: boolean;
  error: string | null;
  apiHealthy: boolean;
  dbConnected: boolean;
  groqConfigured: boolean;
  groqStatus: string;
  groqModel: string;
  selectDataset: (id: string) => Promise<void>;
  refreshDatasets: () => Promise<void>;
  testGroq: (model?: string) => Promise<AITestConnectionResponse>;
}

const DatasetContext = createContext<DatasetContextType>({
  activeDataset: null,
  datasets: [],
  scopes: null,
  loading: true,
  error: null,
  apiHealthy: false,
  dbConnected: false,
  groqConfigured: false,
  groqStatus: "Checking...",
  groqModel: "openai/gpt-oss-20b",
  selectDataset: async () => {},
  refreshDatasets: async () => {},
  testGroq: async () => ({ success: false, status: "Checking...", message: "" }),
});

export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [scopes, setScopes] = useState<AnalyticsScopes | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [apiHealthy, setApiHealthy] = useState<boolean>(false);
  const [dbConnected, setDbConnected] = useState<boolean>(false);
  const [groqConfigured, setGroqConfigured] = useState<boolean>(false);
  const [groqStatus, setGroqStatus] = useState<string>("Checking...");
  const [groqModel, setGroqModel] = useState<string>("openai/gpt-oss-20b");

  const refreshDatasets = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check health
      try {
        const health = await api.getHealth();
        setApiHealthy(health.status === "online");
        setDbConnected(health.db_connected === true);
        setGroqConfigured(health.groq_configured);
        setGroqStatus(health.groq_status || (health.groq_configured ? "API Key Configured" : "API Key Missing"));
        if (health.groq_model) setGroqModel(health.groq_model);
      } catch {
        setApiHealthy(false);
        setDbConnected(false);
        setGroqStatus("Backend Offline");
      }

      // Fetch scopes
      try {
        const sc = await api.getScopes();
        setScopes(sc);
      } catch {
        // Fallback
      }

      const list = await api.getDatasets();
      setDatasets(list);

      const active = list.find((d) => d.is_active) || list[0] || null;
      setActiveDataset(active);
    } catch (err: any) {
      setError(err.message || "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  };

  const selectDataset = async (id: string) => {
    try {
      const activated = await api.activateDataset(id);
      setActiveDataset(activated);
      setDatasets((prev) =>
        prev.map((d) => ({
          ...d,
          is_active: d.id === id,
        }))
      );
      // Refresh scopes
      api.getScopes().then(setScopes).catch(() => {});
    } catch (err: any) {
      setError(err.message || "Failed to activate dataset");
    }
  };

  const testGroq = async (model?: string): Promise<AITestConnectionResponse> => {
    try {
      const res = await api.testGroqConnection(model || groqModel);
      setGroqStatus(res.status);
      if (res.model) setGroqModel(res.model);
      return res;
    } catch (err: any) {
      const errRes: AITestConnectionResponse = {
        success: false,
        status: "Groq Temporarily Unavailable",
        message: err.message || "Connection failed.",
      };
      setGroqStatus(errRes.status);
      return errRes;
    }
  };

  useEffect(() => {
    refreshDatasets();
  }, []);

  return (
    <DatasetContext.Provider
      value={{
        activeDataset,
        datasets,
        scopes,
        loading,
        error,
        apiHealthy,
        dbConnected,
        groqConfigured,
        groqStatus,
        groqModel,
        selectDataset,
        refreshDatasets,
        testGroq,
      }}
    >
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset() {
  return useContext(DatasetContext);
}
