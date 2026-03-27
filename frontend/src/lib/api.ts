import axios, { AxiosInstance, AxiosError } from "axios";
import type { CreateAssetData, UpdateAssetData } from "@/types/assets";
import type { AuthResponse, User } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PensionPlanUpdateData {
  name?: string;
  targetRetirementAge?: number;
  currentAge?: number;
  monthlyContribution?: number;
  expectedReturn?: number;
  currentSavings?: number;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem("token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem("token");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      },
    );
  }

  // Auth endpoints
  async register(username: string, email: string, password: string) {
    const response = await this.client.post("/auth/register", {
      username,
      email,
      password,
    });
    return response.data;
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const payload = new URLSearchParams();
    payload.set("username", email);
    payload.set("password", password);

    const response = await this.client.post("/auth/token", payload, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get("/auth/me");
    return response.data;
  }

  // Portfolio endpoints
  async getPortfolios() {
    const response = await this.client.get("/portfolios");
    return response.data;
  }

  async getPortfolio(id: string) {
    const response = await this.client.get(`/portfolios/${id}`);
    return response.data;
  }

  async createPortfolio(data: { name: string; description?: string }) {
    const response = await this.client.post("/portfolios", data);
    return response.data;
  }

  async updatePortfolio(
    id: string,
    data: { name: string; description?: string },
  ) {
    const response = await this.client.put(`/portfolios/${id}`, data);
    return response.data;
  }

  async deletePortfolio(id: string) {
    const response = await this.client.delete(`/portfolios/${id}`);
    return response.data;
  }

  // Asset endpoints
  async getAssets(portfolioId: string) {
    const response = await this.client.get(`/portfolios/${portfolioId}/assets`);
    return response.data;
  }

  async getAsset(portfolioId: string, assetId: string) {
    const response = await this.client.get(
      `/portfolios/${portfolioId}/assets/${assetId}`,
    );
    return response.data;
  }

  async createAsset(portfolioId: string, data: CreateAssetData) {
    const response = await this.client.post(
      `/portfolios/${portfolioId}/assets`,
      data,
    );
    return response.data;
  }

  async updateAsset(
    portfolioId: string,
    assetId: string,
    data: UpdateAssetData,
  ) {
    const response = await this.client.put(
      `/portfolios/${portfolioId}/assets/${assetId}`,
      data,
    );
    return response.data;
  }

  async deleteAsset(portfolioId: string, assetId: string) {
    const response = await this.client.delete(
      `/portfolios/${portfolioId}/assets/${assetId}`,
    );
    return response.data;
  }

  async getSentimentHistory(symbol: string, days: number = 7) {
    const response = await this.client.get(
      `/sentiment/history/${symbol}?days=${days}`,
    );
    return response.data;
  }

  // Currency conversion endpoints
  async convertCurrency(from: string, to: string, amount: number) {
    const response = await this.client.post("/currency/convert", {
      from,
      to,
      amount,
    });
    return response.data;
  }

  async getExchangeRates(base: string = "USD") {
    const response = await this.client.get(`/currency/rates?base=${base}`);
    return response.data;
  }

  async getSupportedCurrencies() {
    const response = await this.client.get("/currency/supported");
    return response.data;
  }

  // Insurance recommendation endpoints
  async getInsuranceRecommendations(userData: {
    age: number;
    income: number;
    dependents: number;
    hasHealthInsurance: boolean;
    hasLifeInsurance: boolean;
    riskTolerance: "low" | "medium" | "high";
  }) {
    const response = await this.client.post(
      "/insurance/recommendations",
      userData,
    );
    return response.data;
  }

  async getInsuranceProducts() {
    const response = await this.client.get("/insurance/products");
    return response.data;
  }

  // Pension planning endpoints
  async getPensionPlans() {
    const response = await this.client.get("/pension/plans");
    return response.data;
  }

  async getPensionPlan(id: string) {
    const response = await this.client.get(`/pension/plans/${id}`);
    return response.data;
  }

  async createPensionPlan(data: {
    name: string;
    targetRetirementAge: number;
    currentAge: number;
    monthlyContribution: number;
    expectedReturn: number;
    currentSavings?: number;
  }) {
    const response = await this.client.post("/pension/plans", data);
    return response.data;
  }

  async updatePensionPlan(id: string, data: PensionPlanUpdateData) {
    const response = await this.client.put(`/pension/plans/${id}`, data);
    return response.data;
  }

  async deletePensionPlan(id: string) {
    const response = await this.client.delete(`/pension/plans/${id}`);
    return response.data;
  }

  async calculatePensionProjection(data: {
    currentAge: number;
    retirementAge: number;
    monthlyContribution: number;
    currentSavings: number;
    expectedReturn: number;
  }) {
    const response = await this.client.post("/pension/calculate", data);
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
