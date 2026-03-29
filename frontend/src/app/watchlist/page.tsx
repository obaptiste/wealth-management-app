"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import {
  Box,
  Button,
  Card as ChakraCard,
  CardBody,
  CardHeader,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  Input,
  Skeleton,
  SkeletonText,
  Stack,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Textarea,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  WatchlistSignalPanel,
  WatchlistSignalPanelSkeleton,
} from "@/components/dashboard/WatchlistSignalPanel";
import apiClient from "@/lib/api";
import {
  buildWatchlistSignalItems,
  type RawWatchlistItem,
} from "@/services/watchlist-signals";
import type { WatchlistSignalItem } from "@/types/domain";

type WatchlistPageState =
  | { status: "loading" }
  | { status: "error"; message: string; items: WatchlistSignalItem[] }
  | { status: "success"; items: WatchlistSignalItem[] };

interface WatchlistFormState {
  symbol: string;
  display_name: string;
  notes: string;
}

const INITIAL_FORM_STATE: WatchlistFormState = {
  symbol: "",
  display_name: "",
  notes: "",
};

function toSignalItems(items: RawWatchlistItem[]): WatchlistSignalItem[] {
  return buildWatchlistSignalItems(items);
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "data" in error.response &&
    typeof error.response.data === "object" &&
    error.response.data !== null &&
    "detail" in error.response.data &&
    typeof error.response.data.detail === "string"
  ) {
    return error.response.data.detail;
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

function formatAddedAt(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function formatSignalLabel(item: WatchlistSignalItem): string {
  return item.latest_sentiment?.label.replace(/_/g, " ") ?? "No signal";
}

export default function WatchlistPage() {
  const [state, setState] = useState<WatchlistPageState>({ status: "loading" });
  const [form, setForm] = useState<WatchlistFormState>(INITIAL_FORM_STATE);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [removingSymbol, setRemovingSymbol] = useState<string | null>(null);

  async function refreshWatchlist(): Promise<WatchlistSignalItem[]> {
    const items = (await apiClient.getWatchlist()) as RawWatchlistItem[];
    const signalItems = toSignalItems(items);
    setState({ status: "success", items: signalItems });
    return signalItems;
  }

  useEffect(() => {
    let active = true;

    async function loadWatchlist(): Promise<void> {
      try {
        const items = (await apiClient.getWatchlist()) as RawWatchlistItem[];

        if (!active) {
          return;
        }

        setState({ status: "success", items: toSignalItems(items) });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          status: "error",
          message: getErrorMessage(error, "Watchlist could not be loaded."),
          items: [],
        });
      }
    }

    void loadWatchlist();

    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const symbol = form.symbol.trim().toUpperCase();

    if (!symbol) {
      setFormError("Symbol is required.");
      return;
    }

    setSubmitting(true);
    setFormError(null);

    try {
      await apiClient.addToWatchlist({
        symbol,
        display_name: form.display_name.trim() || undefined,
        notes: form.notes.trim() || undefined,
      });

      await refreshWatchlist();
      setForm(INITIAL_FORM_STATE);
    } catch (error) {
      setFormError(
        getErrorMessage(error, "The symbol could not be added right now."),
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemove(symbol: string): Promise<void> {
    setRemovingSymbol(symbol);
    setFormError(null);

    try {
      await apiClient.removeFromWatchlist(symbol);
      await refreshWatchlist();
    } catch (error) {
      setFormError(
        getErrorMessage(error, `The symbol ${symbol} could not be removed.`),
      );
    } finally {
      setRemovingSymbol(null);
    }
  }

  const signalPanel =
    state.status === "loading" ? (
      <WatchlistSignalPanelSkeleton />
    ) : (
      <WatchlistSignalPanel
        data={
          state.status === "error"
            ? { status: "error", items: [] }
            : { status: "available", items: state.items }
        }
      />
    );

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
            <Stack gap={0}>
              <Heading size="lg">OpenBank Wealth Management</Heading>
              <Text color="gray.500">Track symbols and sentiment signals</Text>
            </Stack>
            <ThemeToggle />
          </Flex>
        </Box>

        <Container maxW="container.xl" py={8}>
          <Flex
            justify="space-between"
            align={{ base: "start", md: "center" }}
            direction={{ base: "column", md: "row" }}
            gap={4}
            mb={6}
          >
            <Stack gap={1}>
              <Heading>Watchlist</Heading>
              <Text color="gray.500">
                Add symbols you want to monitor and remove them when they are no
                longer relevant.
              </Text>
            </Stack>

            <Button as={Link} href="/dashboard" variant="outline">
              Back To Dashboard
            </Button>
          </Flex>

          <Stack gap={8}>
            {signalPanel}

            <ChakraCard>
              <CardHeader>
                <Heading size="md">Add Symbol</Heading>
              </CardHeader>
              <CardBody>
                <Box
                  as="form"
                  onSubmit={(event: FormEvent<HTMLFormElement>) =>
                    void handleSubmit(event)
                  }
                >
                  <Stack gap={4}>
                    <FormControl isRequired>
                      <FormLabel>Symbol</FormLabel>
                      <Input
                        placeholder="AAPL"
                        value={form.symbol}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            symbol: event.target.value,
                          }))
                        }
                        maxLength={20}
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel>Display Name</FormLabel>
                      <Input
                        placeholder="Apple"
                        value={form.display_name}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            display_name: event.target.value,
                          }))
                        }
                        maxLength={100}
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel>Notes</FormLabel>
                      <Textarea
                        placeholder="Why this symbol matters"
                        value={form.notes}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            notes: event.target.value,
                          }))
                        }
                        rows={3}
                      />
                    </FormControl>

                    {formError ? <Text color="red.500">{formError}</Text> : null}

                    <HStack justify="flex-end">
                      <Button type="submit" colorScheme="primary" isLoading={submitting}>
                        Add To Watchlist
                      </Button>
                    </HStack>
                  </Stack>
                </Box>
              </CardBody>
            </ChakraCard>

            <ChakraCard>
              <CardHeader>
                <Heading size="md">Tracked Symbols</Heading>
              </CardHeader>
              <CardBody>
                {state.status === "loading" ? (
                  <Stack gap={4}>
                    <Skeleton height="24px" width="30%" />
                    <SkeletonText noOfLines={5} spacing={4} skeletonHeight={3} />
                  </Stack>
                ) : state.items.length === 0 ? (
                  <Text color="gray.500">
                    No symbols are being tracked yet. Add one above to start the
                    watchlist.
                  </Text>
                ) : (
                  <TableContainer>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Symbol</Th>
                          <Th>Display Name</Th>
                          <Th>Signal</Th>
                          <Th>Added</Th>
                          <Th>Notes</Th>
                          <Th textAlign="right">Action</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {state.items.map((item) => (
                          <Tr key={item.symbol}>
                            <Td fontWeight="semibold">{item.symbol}</Td>
                            <Td>{item.display_name ?? "Not set"}</Td>
                            <Td>{formatSignalLabel(item)}</Td>
                            <Td>{formatAddedAt(item.added_at)}</Td>
                            <Td>{item.notes ?? "None"}</Td>
                            <Td textAlign="right">
                              <Button
                                colorScheme="red"
                                variant="ghost"
                                size="sm"
                                onClick={() => void handleRemove(item.symbol)}
                                isLoading={removingSymbol === item.symbol}
                              >
                                Remove
                              </Button>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                )}
              </CardBody>
            </ChakraCard>
          </Stack>
        </Container>
      </Box>
    </Box>
  );
}
