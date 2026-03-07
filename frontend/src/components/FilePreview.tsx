import { Box, HStack, IconButton, Text, Stack } from "@chakra-ui/react";
import { ChevronLeftIcon, ChevronRightIcon, ExternalLinkIcon } from "@chakra-ui/icons";
import { useMemo } from "react";
import type { BatchItem, FileResult } from "../lib/api";

function isPdf(name: string) {
  return name.toLowerCase().endsWith(".pdf");
}

type FilePreviewProps = {
  items: BatchItem[];
  index: number;
  onPrev: () => void;
  onNext: () => void;
};

export default function FilePreview({ items, index, onPrev, onNext }: FilePreviewProps) {
  const current = items[index];
  const result = current?.result as FileResult | null;
  const filename = current?.filename || result?.output_filename || "Документ";
  const pdf = result?.output_filename ? isPdf(result.output_filename) : false;

  const preview = useMemo(() => {
    if (!result) return null;
    if (pdf && result.download_url) {
      return (
        <Stack spacing={3}>
          <Box
            as="iframe"
            title="PDF preview"
            src={result.download_url}
            width="100%"
            height="420px"
            borderRadius="12px"
            border="1px solid"
            borderColor="gray.200"
            bg="white"
          />
          {result.preview_text ? (
            <Box
              border="1px solid"
              borderColor="gray.200"
              borderRadius="12px"
              p={3}
              bg="white"
              maxH="200px"
              overflow="auto"
              whiteSpace="pre-wrap"
              fontSize="sm"
              color="gray.700"
            >
              {result.preview_text}
            </Box>
          ) : null}
        </Stack>
      );
    }
    return (
      <Box
        border="1px solid"
        borderColor="gray.200"
        borderRadius="12px"
        p={4}
        bg="white"
        maxH="360px"
        overflow="auto"
        whiteSpace="pre-wrap"
        fontSize="sm"
        color="gray.700"
      >
        {result.preview_text || ""}
      </Box>
    );
  }, [result, pdf]);

  if (!current) return null;

  return (
    <Box>
      <HStack justify="space-between" align="center" mb={3}>
        <HStack spacing={2}>
          <IconButton
            aria-label="Предыдущий документ"
            icon={<ChevronLeftIcon />}
            onClick={onPrev}
            isDisabled={index === 0}
            variant="outline"
            size="sm"
          />
          <IconButton
            aria-label="Следующий документ"
            icon={<ChevronRightIcon />}
            onClick={onNext}
            isDisabled={index >= items.length - 1}
            variant="outline"
            size="sm"
          />
          <Text fontWeight="600" fontSize="sm">
            {index + 1} / {items.length}
          </Text>
        </HStack>
        {result?.download_url ? (
          <HStack spacing={2}>
            <ExternalLinkIcon color="brand.500" />
            <Text as="a" href={result.download_url} fontSize="sm" color="brand.600">
              Скачать
            </Text>
          </HStack>
        ) : null}
      </HStack>
      <Text fontWeight="600" mb={2}>
        {filename}
      </Text>
      {current.error ? (
        <Box borderRadius="12px" border="1px solid" borderColor="red.200" p={4} bg="red.50">
          <Text fontSize="sm" color="red.600">
            Ошибка: {current.error}
          </Text>
        </Box>
      ) : (
        preview
      )}
    </Box>
  );
}
