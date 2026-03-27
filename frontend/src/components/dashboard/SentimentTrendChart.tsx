"use client";

import {
  Box,
  Card as ChakraCard,
  CardBody,
  CardHeader,
  Heading,
  Skeleton,
  SkeletonText,
  Stack,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SentimentChartPoint } from "@/types/chart";

interface SentimentTrendChartProps {
  data: SentimentChartPoint[];
}

function formatScore(score: number): string {
  const percent = Math.round(score * 100);
  const prefix = percent > 0 ? "+" : "";
  return `${prefix}${percent}%`;
}

function formatLabel(date: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
  }).format(new Date(`${date}T00:00:00Z`));
}

export function SentimentTrendChartSkeleton() {
  return (
    <ChakraCard>
      <CardHeader>
        <Heading size="md">Sentiment Trend</Heading>
      </CardHeader>
      <CardBody>
        <Skeleton height="260px" borderRadius="lg" />
        <SkeletonText mt={4} noOfLines={2} spacing={3} skeletonHeight={3} />
      </CardBody>
    </ChakraCard>
  );
}

export function SentimentTrendChart({ data }: SentimentTrendChartProps) {
  const cardBg = useColorModeValue("white", "gray.800");
  const chartGrid = useColorModeValue(
    "rgba(15, 23, 42, 0.08)",
    "rgba(226, 232, 240, 0.12)",
  );
  const axisColor = useColorModeValue("#475569", "#CBD5E1");
  const tooltipBg = useColorModeValue("#FFFFFF", "#0F172A");
  const tooltipBorder = useColorModeValue("#CBD5E1", "#334155");
  const emptyBg = useColorModeValue("gray.50", "gray.700");

  if (data.length === 0) {
    return (
      <ChakraCard bg={cardBg}>
        <CardHeader>
          <Heading size="md">Sentiment Trend</Heading>
        </CardHeader>
        <CardBody>
          <Box borderRadius="lg" bg={emptyBg} px={6} py={10}>
            <Stack gap={3}>
              <Text fontWeight="semibold">No sentiment history yet</Text>
              <Text color="gray.500">
                Stored sentiment results for the lead holding will appear here
                once data has been analyzed.
              </Text>
            </Stack>
          </Box>
        </CardBody>
      </ChakraCard>
    );
  }

  return (
    <ChakraCard bg={cardBg}>
      <CardHeader>
        <Heading size="md">Sentiment Trend</Heading>
      </CardHeader>
      <CardBody>
        <Box width="100%" height="280px">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 16, right: 16, bottom: 0, left: 0 }}
            >
              <defs>
                <linearGradient
                  id="sentimentScoreFill"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="5%" stopColor="#00AC74" stopOpacity={0.28} />
                  <stop offset="95%" stopColor="#00AC74" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid
                stroke={chartGrid}
                strokeDasharray="3 3"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                stroke={axisColor}
                tickFormatter={formatLabel}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke={axisColor}
                domain={[-1, 1]}
                tickFormatter={formatScore}
                tickLine={false}
                axisLine={false}
                width={48}
              />
              <ReferenceLine y={0} stroke={axisColor} strokeDasharray="4 4" />
              <Tooltip
                contentStyle={{
                  backgroundColor: tooltipBg,
                  border: `1px solid ${tooltipBorder}`,
                  borderRadius: "12px",
                }}
                formatter={(value: number, key: string) => {
                  if (key === "score") {
                    return [formatScore(value), "Net sentiment"];
                  }

                  return [`${value.toFixed(0)}%`, key];
                }}
                labelFormatter={(value) => formatLabel(String(value))}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#00AC74"
                strokeWidth={3}
                fill="url(#sentimentScoreFill)"
                fillOpacity={1}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Box>

        <Text color="gray.500" mt={4}>
          Net sentiment is calculated from positive minus negative share of
          analyzed entries.
        </Text>
      </CardBody>
    </ChakraCard>
  );
}
