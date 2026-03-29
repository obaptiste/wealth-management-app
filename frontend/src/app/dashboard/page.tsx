"use client";

import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Stack,
  Text,
} from "@chakra-ui/react";
import { loadDashboardData, type DashboardData } from "@/app/dashboard/data";
import {
  DashboardSummaryCards,
  DashboardSummaryCardsSkeleton,
} from "@/components/dashboard/DashboardSummaryCards";
import {
  SentimentTrendChart,
  SentimentTrendChartSkeleton,
} from "@/components/dashboard/SentimentTrendChart";
import {
  WatchlistSignalPanel,
  WatchlistSignalPanelSkeleton,
} from "@/components/dashboard/WatchlistSignalPanel";
import { ThemeToggle } from "@/components/ThemeToggle";

type DashboardLoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: DashboardData };

export default function Dashboard() {
  const [state, setState] = useState<DashboardLoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    async function fetchDashboard(): Promise<void> {
      try {
        const data = await loadDashboardData();

        if (!active) {
          return;
        }

        setState({ status: "success", data });
      } catch (error) {
        if (!active) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Dashboard data could not be loaded.";

        setState({ status: "error", message });
      }
    }

    void fetchDashboard();

    return () => {
      active = false;
    };
  }, []);

  const content = (() => {
    if (state.status === "loading") {
      return (
        <Stack gap={8}>
          <DashboardSummaryCardsSkeleton />
          <SentimentTrendChartSkeleton />
          <WatchlistSignalPanelSkeleton />
        </Stack>
      );
    }

    if (state.status === "error") {
      return (
        <Stack gap={4}>
          <Heading size="md">Dashboard unavailable</Heading>
          <Text color="red.500">{state.message}</Text>
          <Text color="gray.500">
            This usually means the API is offline, authentication is missing, or
            portfolio data has not been created yet.
          </Text>
        </Stack>
      );
    }

    return (
      <Stack gap={8}>
        <DashboardSummaryCards data={state.data} />
        <SentimentTrendChart data={state.data.sentiment_trend} />
        <WatchlistSignalPanel data={state.data.watchlist} />
      </Stack>
    );
  })();

  return (
    <Box
      borderWidth="1px"
      borderRadius="lg"
      overflow="hidden"
      boxShadow="md"
      bg="white"
      _dark={{ bg: "gray.800" }}
    >
      <Box minH="100vh" w="full">
        <Box as="header" py={4} px={6} borderBottomWidth="1px">
          <Flex
            justify="space-between"
            align="center"
            maxW="container.xl"
            mx="auto"
          >
            <Heading size="lg">OpenBank Wealth Management</Heading>
            <ThemeToggle />
          </Flex>
        </Box>

        <Container maxW="container.xl" py={8}>
          <Heading mb={6}>Dashboard</Heading>
          {content}

          <Flex gap={6} flexDirection={{ base: "column", md: "row" }} mt={8}>
            <Button colorScheme="primary" size="lg">
              Add Asset
            </Button>
            <Button colorScheme="secondary" size="lg">
              View Reports
            </Button>
          </Flex>
        </Container>
      </Box>
    </Box>
  );
}
