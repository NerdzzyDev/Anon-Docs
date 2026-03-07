import {
  Box,
  Button,
  Checkbox,
  Container,
  Divider,
  Flex,
  Grid,
  Heading,
  HStack,
  Icon,
  IconButton,
  Input,
  Progress,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  Textarea,
  useToast,
} from "@chakra-ui/react";
import { chakra } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { FiCheck, FiCopy, FiDownload, FiEye, FiFileText, FiRefreshCw, FiUploadCloud } from "react-icons/fi";
import {
  anonymizeFile,
  anonymizeText,
  getBatchStatus,
  startBatch,
  type AnonymizeOptions,
  type BatchItem,
  type FileResult,
} from "./lib/api";

const defaultOptions: AnonymizeOptions = {
  fio: true,
  passport: true,
  birthdate: true,
  snils_inn: true,
  phone: true,
  banking: true,
};

const MotionBox = chakra(motion.div);

const cardBase = {
  borderRadius: "20px",
  bg: "white",
  border: "1px solid",
  borderColor: "steel.200",
  boxShadow: "0 16px 34px rgba(18, 38, 63, 0.08)",
};

function EmptyState() {
  return (
    <Box
      border="1px solid"
      borderColor="steel.200"
      borderRadius="16px"
      p={6}
      bg="linear-gradient(135deg, #f8fbff 0%, #f4f7fd 100%)"
      h="100%"
      position="relative"
      overflow="hidden"
    >
      <Box
        position="absolute"
        inset={0}
        opacity={0.4}
        backgroundImage="radial-gradient(circle at 20% 20%, #dbe8ff 0, transparent 55%), radial-gradient(circle at 80% 0%, #e7f0ff 0, transparent 60%)"
      />
      <Stack spacing={3} align="center" justify="center" h="100%" position="relative">
        <Box
          w="62px"
          h="62px"
          borderRadius="18px"
          bg="brand.50"
          display="grid"
          placeItems="center"
          boxShadow="0 12px 20px rgba(47, 91, 234, 0.18)"
        >
          <FiUploadCloud size={30} color="#2f5bea" />
        </Box>
        <Text fontWeight="600">Здесь появится обработанный текст</Text>
        <Text fontSize="sm" color="gray.500" textAlign="center">
          Результат с подсветкой замен появится сразу после обработки.
        </Text>
      </Stack>
    </Box>
  );
}

export default function App() {
  const toast = useToast();
  const [mode, setMode] = useState<"file" | "text">("file");
  const [options, setOptions] = useState<AnonymizeOptions>(defaultOptions);
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("Здесь появится обработанный текст.");
  const [highlightHtml, setHighlightHtml] = useState("");
  const [resultPath, setResultPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("Выберите документ или текст для обработки");
  const [fileWarning, setFileWarning] = useState("");
  const [resultItems, setResultItems] = useState<BatchItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [isHighlightOpen, setIsHighlightOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const batchTimer = useRef<number | null>(null);

  const optionAllSelected = useMemo(() => Object.values(options).every(Boolean), [options]);

  const currentFileName = useMemo(() => {
    const files = fileRef.current?.files;
    if (!files || files.length === 0) return "Файлы не выбраны";
    if (files.length === 1) return files[0].name;
    return `${files.length} файла(ов) выбрано`;
  }, [fileRef.current?.files?.length]);

  useEffect(() => {
    return () => {
      if (batchTimer.current) {
        window.clearInterval(batchTimer.current);
      }
    };
  }, []);

  const updateOption = (key: keyof AnonymizeOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleAll = () => {
    if (optionAllSelected) {
      setOptions({
        fio: false,
        passport: false,
        birthdate: false,
        snils_inn: false,
        phone: false,
        banking: false,
      });
    } else {
      setOptions({ ...defaultOptions });
    }
  };

  const runText = async () => {
    if (!inputText.trim()) {
      toast({ status: "warning", title: "Введите текст для обработки" });
      return;
    }
    setBusy(true);
    setProgress(18);
    setStatus("Обработка текста...");
    try {
      const data = await anonymizeText({ text: inputText, options });
      const result: FileResult = {
        result_path: data.result_path || "",
        download_url: "",
        output_filename: "text.txt",
        preview_html: data.highlighted_html || "",
        preview_text: data.anonymized_text || "",
        warnings: [],
      };
      const item: BatchItem = { filename: "Текстовый результат", result, error: null };
      setResultItems([item]);
      setSelectedIds(new Set([item.filename]));
      setActiveItemId(item.filename);
      setOutputText(result.preview_text || "Обработка завершена.");
      setHighlightHtml(result.preview_html || "");
      setResultPath(result.result_path || "");
      setStatus("Готово");
      setProgress(100);
    } catch (error: any) {
      setStatus("Ошибка обработки");
      setProgress(0);
      toast({ status: "error", title: error.message || "Ошибка обработки" });
    } finally {
      setBusy(false);
    }
  };

  const runFile = async () => {
    const files = fileRef.current?.files;
    if (!files || files.length === 0) {
      toast({ status: "warning", title: "Выберите файл" });
      return;
    }

    if (batchTimer.current) {
      window.clearInterval(batchTimer.current);
    }

    setBusy(true);
    setProgress(12);
    setStatus("Обработка файлов...");
    setFileWarning("");
    setResultItems([]);
    setSelectedIds(new Set());
    setActiveItemId(null);

    try {
      if (files.length === 1) {
        const result = await anonymizeFile(files[0], options);
        setOutputText(result.preview_text || "Файл обработан.");
        setHighlightHtml(result.preview_html || "");
        setResultPath(result.result_path || "");
        const item: BatchItem = {
          filename: files[0].name,
          result,
          error: null,
        };
        setResultItems([item]);
        setSelectedIds(new Set([files[0].name]));
        setActiveItemId(files[0].name);
        setStatus("Файл обработан");
        setProgress(100);
        if (result.warnings?.length) setFileWarning(result.warnings.join(" "));
        return;
      }

      const batch = await startBatch(Array.from(files), options);
      setStatus("Пакетная обработка запущена");
      setResultPath(`Задача: ${batch.job_id}`);

      batchTimer.current = window.setInterval(async () => {
        try {
          const statusData = await getBatchStatus(batch.job_id);
          setProgress(statusData.progress || 0);
          setStatus(`Пакет: ${statusData.processed}/${statusData.total}`);

          if (statusData.status === "completed") {
            if (batchTimer.current) window.clearInterval(batchTimer.current);
            const items = statusData.items || [];
            setResultItems(items);
            const first = items?.[0]?.result || null;
            setOutputText(first?.preview_text || "");
            setHighlightHtml(first?.preview_html || "");
            const initialIds = new Set(items.map((item) => item.filename));
            setSelectedIds(initialIds);
            setActiveItemId(items[0]?.filename || null);
            const hasWarnings = statusData.items?.some((item) => item.result?.warnings?.length);
            const hasErrors = statusData.items?.some((item) => item.error);
            if (hasErrors) {
              setFileWarning("Некоторые файлы обработались с ошибками — см. список.");
            } else if (hasWarnings) {
              setFileWarning("Некоторые файлы вернули предупреждения — см. список ниже.");
            }
            setStatus("Пакет обработан");
            setProgress(100);
            setBusy(false);
          }
        } catch (err: any) {
          if (batchTimer.current) window.clearInterval(batchTimer.current);
          setBusy(false);
          setStatus("Ошибка пакетной обработки");
          setProgress(0);
          toast({ status: "error", title: err.message || "Ошибка пакетной обработки" });
        }
      }, 800);
    } catch (error: any) {
      setStatus("Ошибка обработки");
      setProgress(0);
      toast({ status: "error", title: error.message || "Ошибка" });
    } finally {
      if (files.length === 1) setBusy(false);
    }
  };

  const activeItem = useMemo(() => {
    if (!activeItemId) return null;
    return resultItems.find((item) => item.filename === activeItemId) || null;
  }, [activeItemId, resultItems]);

  const copyResult = async () => {
    const text = activeItem?.result?.preview_text || outputText || "";
    if (!text) {
      toast({ status: "warning", title: "Нет текста для копирования" });
      return;
    }
    await navigator.clipboard.writeText(text);
    toast({ status: "success", title: "Текст скопирован" });
  };

  useEffect(() => {
    if (!activeItemId) return;
    const item = resultItems.find((entry) => entry.filename === activeItemId) || null;
    if (!item || !item.result) return;
    setOutputText(item.result.preview_text || "");
    setHighlightHtml(item.result.preview_html || "");
  }, [activeItemId, resultItems]);

  const resultsAllSelected = selectedIds.size > 0 && selectedIds.size === resultItems.length;
  const toggleAllSelected = () => {
    if (resultsAllSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(resultItems.map((item) => item.filename)));
    }
  };

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const downloadSelected = () => {
    const selected = resultItems.filter((item) => selectedIds.has(item.filename) && item.result?.download_url);
    if (!selected.length) {
      toast({ status: "warning", title: "Нет выбранных файлов для скачивания" });
      return;
    }
    selected.forEach((item) => {
      const link = document.createElement("a");
      link.href = item.result!.download_url;
      link.download = item.result!.output_filename || item.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
    });
  };

  const openHighlight = (item: BatchItem) => {
    if (!item.result) return;
    setActiveItemId(item.filename);
    setHighlightHtml(item.result.preview_html || "");
    setIsHighlightOpen(true);
  };

  return (
    <Container maxW="1180px" h="100vh" py={{ base: 4, lg: 6 }}>
      <Grid templateRows="auto 1fr" h="100%" gap={4}>
        <MotionBox p={{ base: 4, lg: 5 }} borderRadius="22px" bg="whiteAlpha.900" boxShadow="0 18px 36px rgba(18, 38, 63, 0.12)" border="1px solid" borderColor="steel.200" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <Flex justify="space-between" align="center" flexWrap="wrap" gap={3}>
            <Stack spacing={2} maxW="620px">
              <Text fontWeight="700" textTransform="uppercase" fontSize="xs" color="brand.500" letterSpacing="0.2em">
                Сервис анонимизации документов
              </Text>
              <Heading size="md">Анонимизация документов и текстов</Heading>
              <Text color="gray.600" fontSize="sm">
                Единый аккуратный интерфейс для быстрой обработки документов.
              </Text>
            </Stack>
            <Box minW={{ base: "100%", md: "auto" }}>
              <Flex align="center" gap={3} bg="steel.50" p={2} borderRadius="999px" border="1px solid" borderColor="steel.200">
                <Text fontSize="sm" color="gray.600">Документы</Text>
                <Switch size="lg" colorScheme="brand" isChecked={mode === "text"} onChange={() => setMode(mode === "file" ? "text" : "file")} />
                <Text fontSize="sm" color="gray.600">Текст</Text>
              </Flex>
            </Box>
          </Flex>
        </MotionBox>

        <Grid templateColumns={{ base: "1fr", lg: "minmax(360px, 0.9fr) 1.1fr" }} gap={4} h="100%">
          <Stack spacing={4} h="100%">
            <MotionBox {...cardBase} p={4} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.05 }}>
              <Flex justify="space-between" align="center" flexWrap="wrap" gap={2}>
                <Text fontWeight="600">Типы данных</Text>
                <Button size="xs" variant="ghost" colorScheme="brand" onClick={toggleAll} leftIcon={<FiRefreshCw />}>
                  {optionAllSelected ? "Снять все" : "Выбрать все"}
                </Button>
              </Flex>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={2} mt={3}>
                <Checkbox colorScheme="brand" isChecked={options.fio} onChange={() => updateOption("fio")}>ФИО</Checkbox>
                <Checkbox colorScheme="brand" isChecked={options.passport} onChange={() => updateOption("passport")}>Паспортные данные</Checkbox>
                <Checkbox colorScheme="brand" isChecked={options.birthdate} onChange={() => updateOption("birthdate")}>Даты рождения</Checkbox>
                <Checkbox colorScheme="brand" isChecked={options.snils_inn} onChange={() => updateOption("snils_inn")}>СНИЛС / ИНН</Checkbox>
                <Checkbox colorScheme="brand" isChecked={options.phone} onChange={() => updateOption("phone")}>Телефоны</Checkbox>
                <Checkbox colorScheme="brand" isChecked={options.banking} onChange={() => updateOption("banking")}>Счета / реквизиты</Checkbox>
              </SimpleGrid>
            </MotionBox>

            <MotionBox {...cardBase} p={4} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.1 }} flex="1">
              <Stack spacing={3} h="100%">
                <Text fontWeight="600">Источник</Text>
                {mode === "file" ? (
                  <Stack spacing={3} flex="1">
                    <Box
                      border="2px dashed"
                      borderColor="steel.200"
                      borderRadius="18px"
                      p={4}
                      bg="steel.50"
                      position="relative"
                      flex="1"
                      cursor="pointer"
                      _hover={{ borderColor: "brand.300", bg: "steel.100" }}
                      onClick={() => fileRef.current?.click()}
                    >
                      <Input
                        type="file"
                        multiple
                        accept=".txt,.csv,.md,.json,.log,.docx,.xlsx,.xlsm,.pdf,.doc"
                        opacity={0}
                        position="absolute"
                        inset={0}
                        cursor="pointer"
                        ref={fileRef}
                        onChange={() => setResultPath("")}
                      />
                      <Stack spacing={2} align="center" textAlign="center" h="100%" justify="center">
                        <Box w="48px" h="48px" borderRadius="14px" bg="brand.50" display="grid" placeItems="center">
                          <FiUploadCloud color="#2f5bea" size={22} />
                        </Box>
                        <Text fontWeight="600">Загрузить документы</Text>
                        <Text fontSize="sm" color="gray.500">Можно выбрать несколько файлов.</Text>
                        <Text fontSize="sm" color="gray.700">{currentFileName}</Text>
                      </Stack>
                    </Box>
                    <HStack spacing={3} flexWrap="wrap">
                      <Button colorScheme="brand" onClick={runFile} isLoading={busy}>Запустить</Button>
                      <Text fontSize="xs" color="gray.500">PDF, DOCX, XLSX, TXT</Text>
                    </HStack>
                    {fileWarning ? <Text fontSize="xs" color="orange.500">{fileWarning}</Text> : null}
                  </Stack>
                ) : (
                  <Stack spacing={3} flex="1">
                    <Textarea minH={{ base: "180px", lg: "240px" }} bg="white" placeholder="Вставьте текст для анонимизации..." value={inputText} onChange={(event) => setInputText(event.target.value)} />
                    <Button colorScheme="brand" onClick={runText} isLoading={busy}>Запустить</Button>
                  </Stack>
                )}
              </Stack>
            </MotionBox>

            <MotionBox {...cardBase} p={4} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.15 }}>
              <Stack spacing={3}>
                <Flex justify="space-between" align="center">
                  <Text fontWeight="600">Статус</Text>
                  <HStack spacing={2}>
                    <Icon as={FiCheck} color={progress === 100 ? "green.500" : "gray.400"} />
                    <Text fontSize="xs" color="gray.600">{status}</Text>
                  </HStack>
                </Flex>
                <Progress value={progress} colorScheme="brand" borderRadius="full" height="8px" />
              </Stack>
            </MotionBox>
          </Stack>

          <Stack spacing={4} h="100%">
            <MotionBox {...cardBase} p={4} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.1 }} flex="1" overflow="hidden">
              <Stack spacing={3} h="100%">
                <Flex justify="space-between" align="center">
                  <Text fontWeight="600">Результат</Text>
                  <HStack spacing={2}>
                    <IconButton
                      aria-label="Подсветка"
                      icon={<FiEye />}
                      size="sm"
                      variant="outline"
                      onClick={() => setIsHighlightOpen(true)}
                      isDisabled={!activeItem?.result?.preview_html}
                    />
                    <IconButton aria-label="Скопировать" icon={<FiCopy />} size="sm" variant="outline" onClick={copyResult} />
                  </HStack>
                </Flex>
                <Box flex="1" overflow="hidden">
                  {resultItems.length ? (
                    <Stack spacing={3} h="100%">
                      <HStack justify="space-between">
                        <Checkbox isChecked={resultsAllSelected} onChange={toggleAllSelected}>
                          Выбрать все
                        </Checkbox>
                        <Button size="xs" variant="outline" leftIcon={<FiDownload />} onClick={downloadSelected}>
                          Скачать выбранные
                        </Button>
                      </HStack>
                      <Box flex="1" overflow="auto">
                        <Stack spacing={2}>
                          {resultItems.map((item) => {
                            const selected = selectedIds.has(item.filename);
                            const hasError = Boolean(item.error);
                            const warnings = item.result?.warnings?.length ? item.result.warnings.join(" ") : "";
                            return (
                              <Flex
                                key={item.filename}
                                align="center"
                                justify="space-between"
                                gap={3}
                                p={3}
                                border="1px solid"
                                borderColor={selected ? "brand.200" : "steel.200"}
                                borderRadius="14px"
                                bg={selected ? "brand.50" : "white"}
                              >
                                <HStack spacing={3} flex="1">
                                  <Checkbox isChecked={selected} onChange={() => toggleSelected(item.filename)} />
                                  <Stack spacing={0} flex="1">
                                    <Text fontWeight="600" fontSize="sm">
                                      {item.filename}
                                    </Text>
                                    {hasError ? (
                                      <Text fontSize="xs" color="red.500">
                                        Ошибка обработки
                                      </Text>
                                    ) : warnings ? (
                                      <Text fontSize="xs" color="orange.500">
                                        {warnings}
                                      </Text>
                                    ) : (
                                      <Text fontSize="xs" color="gray.500">
                                        Готово
                                      </Text>
                                    )}
                                  </Stack>
                                </HStack>
                                <HStack spacing={2}>
                                  <IconButton
                                    aria-label="Просмотр"
                                    icon={<FiEye />}
                                    size="sm"
                                    variant="outline"
                                    onClick={() => openHighlight(item)}
                                    isDisabled={!item.result}
                                  />
                                  <IconButton
                                    aria-label="Скачать"
                                    icon={<FiDownload />}
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      if (!item.result?.download_url) return;
                                      const link = document.createElement("a");
                                      link.href = item.result.download_url;
                                      link.download = item.result.output_filename || item.filename;
                                      document.body.appendChild(link);
                                      link.click();
                                      link.remove();
                                    }}
                                    isDisabled={!item.result?.download_url}
                                  />
                                </HStack>
                              </Flex>
                            );
                          })}
                        </Stack>
                      </Box>
                    </Stack>
                  ) : (
                    <EmptyState />
                  )}
                </Box>
              </Stack>
            </MotionBox>

            <MotionBox {...cardBase} p={4} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.15 }}>
              <Stack spacing={2}>
                <Text fontWeight="600">Путь к результату</Text>
                <Input value={resultPath} readOnly bg="steel.50" />
                <Divider borderColor="steel.200" />
                <Text fontSize="xs" color="gray.500">В пакетном режиме используйте стрелки, чтобы увидеть нужный документ.</Text>
              </Stack>
            </MotionBox>
          </Stack>
        </Grid>
      </Grid>

      {isHighlightOpen ? (
        <Box
          position="fixed"
          inset={0}
          bg="blackAlpha.500"
          display="grid"
          placeItems="center"
          zIndex={10}
          onClick={() => setIsHighlightOpen(false)}
        >
          <Box
            bg="white"
            borderRadius="18px"
            p={5}
            maxW="900px"
            w="90%"
            maxH="80vh"
            overflow="auto"
            boxShadow="0 20px 60px rgba(15, 23, 42, 0.2)"
            onClick={(event) => event.stopPropagation()}
          >
            <Flex justify="space-between" align="center" mb={3}>
              <Text fontWeight="600">Подсветка замен</Text>
              <Button size="sm" variant="outline" onClick={() => setIsHighlightOpen(false)}>
                Закрыть
              </Button>
            </Flex>
            <Box
              border="1px solid"
              borderColor="steel.200"
              borderRadius="14px"
              p={4}
              bg="steel.50"
              dangerouslySetInnerHTML={{ __html: highlightHtml || "<div>Нет данных для подсветки.</div>" }}
            />
          </Box>
        </Box>
      ) : null}
    </Container>
  );
}
