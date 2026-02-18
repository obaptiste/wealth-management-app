'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Input,
  Select,
  Button,
  Card,
  CardBody,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Icon,
  Flex,
  Badge,
  SimpleGrid,
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';
import { TbArrowsExchange, TbTrendingUp, TbCurrencyDollar, TbRefresh } from 'react-icons/tb';
import { apiClient } from '@/lib/api';

const MotionBox = motion(Box);
const MotionCard = motion(Card);

interface ExchangeRate {
  currency: string;
  rate: number;
  name: string;
}

interface ConversionResult {
  from_currency: string;
  to_currency: string;
  amount: number;
  converted_amount: number;
  exchange_rate: number;
  last_updated: string;
}

export default function CurrencyConversionPage() {
  const [fromCurrency, setFromCurrency] = useState('USD');
  const [toCurrency, setToCurrency] = useState('EUR');
  const [amount, setAmount] = useState('1000');
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [rates, setRates] = useState<Record<string, number>>({});
  const [supportedCurrencies, setSupportedCurrencies] = useState<Record<string, string>>({});

  const bgGradient = useColorModeValue(
    'linear(to-br, brand.50, accent.50, slate.100)',
    'linear(to-br, slate.900, slate.800, brand.900)'
  );

  const cardBg = useColorModeValue('white', 'slate.800');
  const accentColor = useColorModeValue('brand.500', 'brand.400');

  useEffect(() => {
    fetchSupportedCurrencies();
    fetchExchangeRates();
  }, []);

  const fetchSupportedCurrencies = async () => {
    try {
      const response = await apiClient.getSupportedCurrencies();
      setSupportedCurrencies(response.currencies);
    } catch (error) {
      console.error('Error fetching supported currencies:', error);
    }
  };

  const fetchExchangeRates = async () => {
    try {
      const response = await apiClient.getExchangeRates(fromCurrency);
      setRates(response.rates);
    } catch (error) {
      console.error('Error fetching exchange rates:', error);
    }
  };

  const handleConvert = async () => {
    if (!amount || parseFloat(amount) <= 0) return;

    setLoading(true);
    try {
      const response = await apiClient.convertCurrency(
        fromCurrency,
        toCurrency,
        parseFloat(amount)
      );
      setResult(response);
    } catch (error) {
      console.error('Error converting currency:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSwap = () => {
    const temp = fromCurrency;
    setFromCurrency(toCurrency);
    setToCurrency(temp);
  };

  const topRates: ExchangeRate[] = Object.entries(rates)
    .filter(([currency]) => ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD'].includes(currency))
    .map(([currency, rate]) => ({
      currency,
      rate,
      name: supportedCurrencies[currency] || currency,
    }))
    .slice(0, 6);

  return (
    <Box minH="100vh" bgGradient={bgGradient} py={8}>
      <Container maxW="container.xl">
        {/* Header */}
        <MotionBox
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <VStack spacing={2} align="start" mb={8}>
            <HStack spacing={3}>
              <Icon as={TbCurrencyDollar} boxSize={10} color={accentColor} />
              <Heading
                size="2xl"
                bgGradient={`linear(to-r, ${accentColor}, accent.500)`}
                bgClip="text"
                fontWeight="800"
              >
                Currency Conversion
              </Heading>
            </HStack>
            <Text fontSize="lg" color="text-secondary">
              Real-time exchange rates for global currencies
            </Text>
          </VStack>
        </MotionBox>

        <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
          {/* Main Conversion Card */}
          <GridItem>
            <MotionCard
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              bg={cardBg}
              shadow="2xl"
            >
              <CardBody p={8}>
                <VStack spacing={6} align="stretch">
                  <Heading size="md">Convert Currency</Heading>

                  {/* Amount Input */}
                  <Box>
                    <Text mb={2} fontWeight="600" color="text-secondary">
                      Amount
                    </Text>
                    <Input
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      size="lg"
                      fontSize="2xl"
                      fontWeight="700"
                      placeholder="Enter amount"
                    />
                  </Box>

                  {/* Currency Selectors */}
                  <HStack spacing={4}>
                    <Box flex={1}>
                      <Text mb={2} fontWeight="600" color="text-secondary">
                        From
                      </Text>
                      <Select
                        value={fromCurrency}
                        onChange={(e) => {
                          setFromCurrency(e.target.value);
                          fetchExchangeRates();
                        }}
                        size="lg"
                      >
                        {Object.entries(supportedCurrencies).map(([code, name]) => (
                          <option key={code} value={code}>
                            {code} - {name}
                          </option>
                        ))}
                      </Select>
                    </Box>

                    <Button
                      onClick={handleSwap}
                      colorScheme="brand"
                      variant="ghost"
                      mt={8}
                      borderRadius="full"
                      p={2}
                      _hover={{ transform: 'rotate(180deg)', transition: 'transform 0.3s' }}
                    >
                      <Icon as={TbArrowsExchange} boxSize={6} />
                    </Button>

                    <Box flex={1}>
                      <Text mb={2} fontWeight="600" color="text-secondary">
                        To
                      </Text>
                      <Select
                        value={toCurrency}
                        onChange={(e) => setToCurrency(e.target.value)}
                        size="lg"
                      >
                        {Object.entries(supportedCurrencies).map(([code, name]) => (
                          <option key={code} value={code}>
                            {code} - {name}
                          </option>
                        ))}
                      </Select>
                    </Box>
                  </HStack>

                  {/* Convert Button */}
                  <Button
                    onClick={handleConvert}
                    isLoading={loading}
                    loadingText="Converting..."
                    colorScheme="brand"
                    size="lg"
                    fontSize="md"
                    fontWeight="700"
                    h={14}
                  >
                    Convert Now
                  </Button>

                  {/* Result Display */}
                  <AnimatePresence>
                    {result && (
                      <MotionBox
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        transition={{ duration: 0.4 }}
                        p={6}
                        borderRadius="xl"
                        bg={useColorModeValue('brand.50', 'brand.900')}
                        borderWidth="2px"
                        borderColor={accentColor}
                      >
                        <VStack spacing={4} align="stretch">
                          <Flex justify="space-between" align="center">
                            <Text fontSize="sm" color="text-muted" fontWeight="600">
                              Converted Amount
                            </Text>
                            <Badge colorScheme="brand" fontSize="xs">
                              Live Rate
                            </Badge>
                          </Flex>
                          <Heading size="2xl" color={accentColor}>
                            {result.converted_amount.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}{' '}
                            <Text as="span" fontSize="xl">
                              {result.to_currency}
                            </Text>
                          </Heading>
                          <Text fontSize="sm" color="text-secondary">
                            1 {result.from_currency} = {result.exchange_rate.toFixed(4)}{' '}
                            {result.to_currency}
                          </Text>
                        </VStack>
                      </MotionBox>
                    )}
                  </AnimatePresence>
                </VStack>
              </CardBody>
            </MotionCard>
          </GridItem>

          {/* Exchange Rates Sidebar */}
          <GridItem>
            <MotionBox
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <VStack spacing={4} align="stretch">
                <Flex justify="space-between" align="center">
                  <Heading size="md">Live Rates</Heading>
                  <Button
                    size="sm"
                    variant="ghost"
                    colorScheme="brand"
                    leftIcon={<Icon as={TbRefresh} />}
                    onClick={fetchExchangeRates}
                  >
                    Refresh
                  </Button>
                </Flex>

                <SimpleGrid columns={1} spacing={3}>
                  {topRates.map((rate, index) => (
                    <MotionCard
                      key={rate.currency}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: 0.3 + index * 0.05 }}
                      bg={cardBg}
                      _hover={{
                        transform: 'translateX(4px)',
                        borderColor: accentColor,
                      }}
                      borderWidth="1px"
                      borderColor="border-primary"
                    >
                      <CardBody p={4}>
                        <Flex justify="space-between" align="center">
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="700" fontSize="lg">
                              {rate.currency}
                            </Text>
                            <Text fontSize="xs" color="text-muted">
                              {rate.name}
                            </Text>
                          </VStack>
                          <VStack align="end" spacing={0}>
                            <Text fontWeight="600" color={accentColor}>
                              {rate.rate.toFixed(4)}
                            </Text>
                            <HStack spacing={1}>
                              <Icon as={TbTrendingUp} boxSize={3} color="success.500" />
                              <Text fontSize="xs" color="success.500">
                                0.2%
                              </Text>
                            </HStack>
                          </VStack>
                        </Flex>
                      </CardBody>
                    </MotionCard>
                  ))}
                </SimpleGrid>
              </VStack>
            </MotionBox>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
