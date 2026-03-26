'use client';

import { useEffect, useState, type ReactNode } from 'react';
import {
  Box,
  Button,
  Card as ChakraCard,
  CardBody,
  Container,
  Flex,
  Heading,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
} from '@chakra-ui/react';
import { loadDashboardData, type DashboardData } from '@/app/dashboard/data';
import { ThemeToggle } from '@/components/ThemeToggle';

type DashboardLoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: DashboardData };

function Card({ children }: { children: ReactNode }) {
  return (
    <Box
      borderWidth="1px"
      borderRadius="lg"
      overflow="hidden"
      boxShadow="md"
      bg="white"
      _dark={{ bg: 'gray.800' }}
    >
      {children}
    </Box>
  );
}

function CardHeader({ children }: { children: ReactNode }) {
  return (
    <Box
      px={4}
      py={2}
      borderBottomWidth="1px"
      bg="gray.50"
      _dark={{ bg: 'gray.700' }}
    >
      {children}
    </Box>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${value.toFixed(1)}%`;
}

export default function Dashboard() {
  const [state, setState] = useState<DashboardLoadState>({ status: 'loading' });

  useEffect(() => {
    let active = true;

    async function fetchDashboard(): Promise<void> {
      try {
        const data = await loadDashboardData();

        if (!active) {
          return;
        }

        setState({ status: 'success', data });
      } catch (error) {
        if (!active) {
          return;
        }

        const message = error instanceof Error
          ? error.message
          : 'Dashboard data could not be loaded.';

        setState({ status: 'error', message });
      }
    }

    void fetchDashboard();

    return () => {
      active = false;
    };
  }, []);

  const content = (() => {
    if (state.status === 'loading') {
      return (
        <Flex minH="320px" align="center" justify="center">
          <Stack align="center" gap={3}>
            <Spinner size="lg" />
            <Text color="gray.500">Loading dashboard data...</Text>
          </Stack>
        </Flex>
      );
    }

    if (state.status === 'error') {
      return (
        <Stack gap={4}>
          <Heading size="md">Dashboard unavailable</Heading>
          <Text color="red.500">{state.message}</Text>
          <Text color="gray.500">
            This usually means the API is offline, authentication is missing, or portfolio data has not been created yet.
          </Text>
        </Stack>
      );
    }

    const { data } = state;
    const sentimentLabel = data.primary_sentiment
      ? data.primary_sentiment.label.replace(/_/g, ' ')
      : 'No sentiment yet';
    const sentimentValue = data.primary_sentiment
      ? formatPercent(data.primary_sentiment.score * 100)
      : 'No tracked signal';
    const sentimentSource = data.primary_sentiment?.symbol
      ? `Latest stored signal for ${data.primary_sentiment.symbol}`
      : 'Add assets with sentiment history to surface a signal';
    const holdingsDescription = data.portfolio_count > 0
      ? `Across ${data.portfolio_count} portfolio${data.portfolio_count === 1 ? '' : 's'}`
      : 'Create a portfolio to start tracking holdings';
    const topAllocation = data.top_allocations[0];
    const allocationDescription = topAllocation
      ? `${topAllocation.symbol} is the largest holding at ${topAllocation.allocation_percent.toFixed(1)}%`
      : 'No holdings available yet';

    return (
      <Stack gap={8}>
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
          <ChakraCard>
            <CardHeader>
              <Heading size="md">Portfolio Value</Heading>
            </CardHeader>
            <CardBody>
              <Heading size="xl">{formatCurrency(data.summary.total_value)}</Heading>
              <Text color={data.summary.total_profit_loss >= 0 ? 'green.500' : 'red.500'}>
                {formatPercent(data.summary.total_profit_loss_percent)} since inception
              </Text>
            </CardBody>
          </ChakraCard>

          <ChakraCard>
            <CardHeader>
              <Heading size="md">Assets</Heading>
            </CardHeader>
            <CardBody>
              <Heading size="xl">{data.asset_count}</Heading>
              <Text>{holdingsDescription}</Text>
            </CardBody>
          </ChakraCard>

          <ChakraCard>
            <CardHeader>
              <Heading size="md">Sentiment Signal</Heading>
            </CardHeader>
            <CardBody>
              <Heading size="xl" textTransform="capitalize">{sentimentLabel}</Heading>
              <Text>{sentimentValue}</Text>
              <Text color="gray.500" mt={2}>{sentimentSource}</Text>
            </CardBody>
          </ChakraCard>
        </SimpleGrid>

        <ChakraCard>
          <CardHeader>
            <Heading size="md">Allocation Highlights</Heading>
          </CardHeader>
          <CardBody>
            <Text fontWeight="medium">{allocationDescription}</Text>
            <Text color="gray.500" mt={2}>
              Profitable positions: {data.metrics.profitable_positions} of {data.metrics.asset_count}
            </Text>
          </CardBody>
        </ChakraCard>
      </Stack>
    );
  })();

  return (
    <Card>
      <Box minH="100vh" w="full">
        <Box as="header" py={4} px={6} borderBottomWidth="1px">
          <Flex justify="space-between" align="center" maxW="container.xl" mx="auto">
            <Heading size="lg">OpenBank Wealth Management</Heading>
            <ThemeToggle />
          </Flex>
        </Box>

        <Container maxW="container.xl" py={8}>
          <Heading mb={6}>Dashboard</Heading>
          {content}

          <Flex gap={6} flexDirection={{ base: 'column', md: 'row' }} mt={8}>
            <Button colorScheme="primary" size="lg">Add Asset</Button>
            <Button colorScheme="secondary" size="lg">View Reports</Button>
          </Flex>
        </Container>
      </Box>
    </Card>
  );
}
