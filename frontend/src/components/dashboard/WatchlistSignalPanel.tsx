"use client";

import {
  Badge,
  Card as ChakraCard,
  CardBody,
  CardHeader,
  Heading,
  HStack,
  SimpleGrid,
  Skeleton,
  SkeletonText,
  Stack,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react";
import type { DashboardData } from "@/app/dashboard/data";
import type {
  WatchlistSignalItem,
  WatchlistSignalStrength,
  WatchlistSignalTrend,
} from "@/types/domain";

interface WatchlistSignalCardProps {
  item: WatchlistSignalItem;
}

function formatTrackedAt(value: string | null): string {
  if (!value) {
    return "Tracking date unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Tracking date unavailable";
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
  }).format(date);
}

function formatSignalScore(score: number | null): string {
  if (score === null) {
    return "Awaiting sentiment data";
  }

  const percent = Math.round(score * 100);
  const prefix = percent > 0 ? "+" : "";

  return `${prefix}${percent}% net sentiment`;
}

function formatTrend(trend: WatchlistSignalTrend): string {
  switch (trend) {
    case "improving":
      return "Improving";
    case "worsening":
      return "Worsening";
    case "steady":
      return "Steady";
    case "unavailable":
      return "Awaiting trend";
    default:
      return "Awaiting trend";
  }
}

function signalBadgeColor(
  strength: WatchlistSignalStrength,
): "red" | "orange" | "yellow" | "gray" {
  switch (strength) {
    case "high":
      return "red";
    case "medium":
      return "orange";
    case "low":
      return "yellow";
    case "none":
      return "gray";
    default:
      return "gray";
  }
}

function sentimentBadgeColor(
  item: WatchlistSignalItem,
): "green" | "yellow" | "red" | "gray" {
  const score = item.latest_sentiment?.score ?? 0;

  if (!item.latest_sentiment) {
    return "gray";
  }

  if (score >= 0.1) {
    return "green";
  }

  if (score <= -0.1) {
    return "red";
  }

  return "yellow";
}

function WatchlistSignalCard({ item }: WatchlistSignalCardProps) {
  const mutedText = useColorModeValue("gray.600", "gray.300");
  const surface = useColorModeValue("gray.50", "gray.700");
  const label = item.display_name ?? item.symbol;

  return (
    <VStack
      align="stretch"
      borderRadius="lg"
      borderWidth="1px"
      bg={surface}
      p={4}
      gap={3}
    >
      <Stack gap={1}>
        <HStack justify="space-between" align="start">
          <Stack gap={0}>
            <Heading size="sm">{label}</Heading>
            <Text color={mutedText} fontSize="sm">
              {item.symbol}
            </Text>
          </Stack>

          <Badge colorScheme={signalBadgeColor(item.signal_strength)}>
            {item.signal_strength} signal
          </Badge>
        </HStack>

        <Text color={mutedText} fontSize="sm">
          Added {formatTrackedAt(item.added_at)}
        </Text>
      </Stack>

      <HStack spacing={3} wrap="wrap">
        <Badge colorScheme={sentimentBadgeColor(item)}>
          {item.latest_sentiment?.label.replace(/_/g, " ") ?? "No signal"}
        </Badge>
        <Text fontSize="sm">{formatSignalScore(item.latest_sentiment?.score ?? null)}</Text>
      </HStack>

      <Text fontSize="sm" color={mutedText}>
        {item.latest_sentiment
          ? `${formatTrend(item.trend)} since the last stored reading`
          : "Sentiment history will appear once analysis has been recorded."}
      </Text>

      {item.notes ? (
        <Text fontSize="sm" color={mutedText}>
          {item.notes}
        </Text>
      ) : null}
    </VStack>
  );
}

export function WatchlistSignalPanelSkeleton() {
  return (
    <ChakraCard>
      <CardHeader>
        <Heading size="md">Watchlist Signals</Heading>
      </CardHeader>
      <CardBody>
        <SimpleGrid columns={{ base: 1, lg: 2 }} gap={4}>
          {[0, 1].map((index) => (
            <Stack key={index} borderWidth="1px" borderRadius="lg" p={4} gap={4}>
              <Skeleton height="20px" width="45%" />
              <SkeletonText noOfLines={3} spacing={3} skeletonHeight={3} />
            </Stack>
          ))}
        </SimpleGrid>
      </CardBody>
    </ChakraCard>
  );
}

export function WatchlistSignalPanel({
  data,
}: {
  data: DashboardData["watchlist"];
}) {
  const emptyBg = useColorModeValue("gray.50", "gray.700");
  const mutedText = useColorModeValue("gray.600", "gray.300");

  if (data.status === "unavailable") {
    return (
      <ChakraCard>
        <CardHeader>
          <Heading size="md">Watchlist Signals</Heading>
        </CardHeader>
        <CardBody>
          <Stack borderRadius="lg" bg={emptyBg} p={6} gap={2}>
            <Text fontWeight="semibold">Watchlist backend not available yet</Text>
            <Text color={mutedText}>
              The dashboard is ready for watchlist signals, but the watchlist
              API is not available in this environment yet.
            </Text>
          </Stack>
        </CardBody>
      </ChakraCard>
    );
  }

  if (data.items.length === 0) {
    return (
      <ChakraCard>
        <CardHeader>
          <Heading size="md">Watchlist Signals</Heading>
        </CardHeader>
        <CardBody>
          <Stack borderRadius="lg" bg={emptyBg} p={6} gap={2}>
            <Text fontWeight="semibold">No watchlist items yet</Text>
            <Text color={mutedText}>
              Add a few symbols to the watchlist to surface tracked sentiment
              signals here.
            </Text>
          </Stack>
        </CardBody>
      </ChakraCard>
    );
  }

  return (
    <ChakraCard>
      <CardHeader>
        <Heading size="md">Watchlist Signals</Heading>
      </CardHeader>
      <CardBody>
        <SimpleGrid columns={{ base: 1, lg: 2 }} gap={4}>
          {data.items.map((item) => (
            <WatchlistSignalCard key={item.symbol} item={item} />
          ))}
        </SimpleGrid>
      </CardBody>
    </ChakraCard>
  );
}
