"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import AppHeader from "../../components/stelgent/AppHeader"; 
// Header bileşeninin doğru path’i buysa, değilse bana yaz düzeltirim.

import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";

import { apiGet } from "@/lib/api";

export default function MintedProjectsPage() {
  const router = useRouter();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  // Kullanıcı bilgisi (token = public key)
  const [user, setUser] = useState(null);

  useEffect(() => {
    const pubKey = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    setUser(pubKey ? { stellar_public_key: pubKey } : null);
  }, []);

  useEffect(() => {
    const fetchMints = async () => {
      try {
        const res = await apiGet("/api/nfts/my");

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          toast.error(
            data.detail || data.error || "Mint edilen projeler alınamadı."
          );
          return;
        }

        const data = await res.json();
        setItems(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("fetch mints error", err);
        toast.error("Mint edilen projeler alınırken hata oluştu.");
      } finally {
        setLoading(false);
      }
    };

    fetchMints();
  }, []);

  const handleDisconnect = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">

      {/* ---------------- HEADER ---------------- */}
      <AppHeader
        currentProject={null}
        user={user}
        onShowProjects={() => router.push("/")}
        onShowSettings={() => router.push("/settings")}
        onDisconnect={handleDisconnect}
      />

      {/* ---------------- PAGE CONTENT ---------------- */}
      <div className="max-w-4xl mx-auto py-10 px-4 space-y-6">
        <h1 className="text-2xl font-semibold">Mint Edilen Projelerim</h1>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center text-sm text-muted-foreground py-12">
            Henüz mint edilmiş projen yok.
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <Card
                key={item.project_id}
                className="p-4 flex flex-col md:flex-row md:justify-between gap-3 bg-gray-800 border-gray-700"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{item.project_title}</span>
                    <Badge variant="outline">
                      Token #{item.token_id}
                    </Badge>
                  </div>

                  <p className="text-xs text-gray-400">
                    Cüzdan:{" "}
                    <span className="font-mono">
                      {item.stellar_address.slice(0, 6)}…{item.stellar_address.slice(-4)}
                    </span>
                  </p>

                  <p className="text-xs text-gray-400">
                    IPFS:{" "}
                    <span className="font-mono">
                      {item.ipfs_cid.slice(0, 6)}…{item.ipfs_cid.slice(-4)}
                    </span>
                  </p>
                </div>

                <Button variant="outline" size="sm" asChild>
                  <a href={item.ipfs_url} target="_blank">
                    <ExternalLink className="w-4 h-4 mr-1" />
                    IPFS’i Aç
                  </a>
                </Button>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
