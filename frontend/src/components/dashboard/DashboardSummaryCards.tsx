"use client";

import {
  Card as ChakraCard,
  CardBody,
  CardHeader,
  Heading,
  SimpleGrid,
  Skeleton,
  SkeletonText,
  Stack,
  Text,
} from "@chakra-ui/react";
import type { DashboardData } from "@/app/dashboard/data";

interface SummaryCardProps {
  title: string;
  primary: string;
  secondary: string;
  accentColor?: string;
  capitalizePrimary?: boolean;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(1)}%`;
}

function SummaryCard({
  title,
  primary,
  secondary,
  accentColor,
  capitalizePrimary = false,
}: SummaryCardProps) {
  return (
    <ChakraCard>
      <CardHeader>
        <Heading size="md">{title}</Heading>
      </CardHeader>
      <CardBody>
        <Heading
          size="xl"
          textTransform={capitalizePrimary ? "capitalize" : undefined}
        >
          {primary}
        </Heading>
        <Text color={accentColor} mt={2}>
          {secondary}
        </Text>
      </CardBody>
    </ChakraCard>
  );
}

export function DashboardSummaryCardsSkeleton() {
  return (
    <Stack gap={8}>
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
        {["Portfolio Value", "Assets", "Sentiment Signal"].map((title) => (
          <ChakraCard key={title}>
            <CardHeader>
              <Heading size="md">{title}</Heading>
            </CardHeader>
            <CardBody>
              <Skeleton height="36px" width="60%" />
              <SkeletonText
                mt={4}
                noOfLines={2}
                spacing={3}
                skeletonHeight={3}
              />
            </CardBody>
          </ChakraCard>
        ))}
      </SimpleGrid>

      <ChakraCard>
        <CardHeader>
          <Heading size="md">Allocation Highlights</Heading>
        </CardHeader>
        <CardBody>
          <SkeletonText noOfLines={2} spacing={4} skeletonHeight={3} />
        </CardBody>
      </ChakraCard>
    </Stack>
  );
}

export function DashboardSummaryCards({ data }: { data: DashboardData }) {
  const hasAssets = data.asset_count > 0;
  const sentimentLabel = data.primary_sentiment
    ? data.primary_sentiment.label.replace(/_/g, " ")
    : "No sentiment yet";
  const sentimentValue = data.primary_sentiment
    ? formatPercent(data.primary_sentiment.score * 100)
    : "No tracked signal";
  const sentimentSource = data.primary_sentiment?.symbol
    ? `Latest stored signal for ${data.primary_sentiment.symbol}`
    : "Add assets with sentiment history to surface a signal";
  const holdingsDescription =
    data.portfolio_count > 0
      ? `Across ${data.portfolio_count} portfolio${data.portfolio_count === 1 ? "" : "s"}`
      : "Create a portfolio to start tracking holdings";
  const topAllocation = data.top_allocations[0];
  const allocationDescription = topAllocation
    ? `${topAllocation.symbol} is the largest holding at ${topAllocation.allocation_percent.toFixed(1)}%`
    : "No holdings available yet";
  const allocationSecondary = hasAssets
    ? `Profitable positions: ${data.metrics.profitable_positions} of ${data.metrics.asset_count}`
    : "Add assets to populate allocation insights";

  return (
    <Stack gap={8}>
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
        <SummaryCard
          title="Portfolio Value"
          primary={formatCurrency(data.summary.total_value)}
          secondary={
            hasAssets
              ? `${formatPercent(data.summary.total_profit_loss_percent)} since inception`
              : "Waiting for portfolio holdings"
          }
          accentColor={
            data.summary.total_profit_loss >= 0 ? "green.500" : "red.500"
          }
        />

        <SummaryCard
          title="Assets"
          primary={String(data.asset_count)}
          secondary={holdingsDescription}
        />

        <SummaryCard
          title="Sentiment Signal"
          primary={sentimentLabel}
          secondary={
            hasAssets
              ? `${sentimentValue} · ${sentimentSource}`
              : "Sentiment appears once holdings exist"
          }
          capitalizePrimary
        />
      </SimpleGrid>

      <SummaryCard
        title="Allocation Highlights"
        primary={allocationDescription}
        secondary={allocationSecondary}
      />
    </Stack>
  );
}
