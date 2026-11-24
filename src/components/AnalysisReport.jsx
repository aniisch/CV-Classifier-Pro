import React, { useEffect, useMemo, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  Typography
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

const PAGE_SIZE = 20;
// Au-dela, les analyses detaillees sont repliees (une par CV) et rendues a la demande
// (400 analyses rendues d'un coup bloquent l'interface).
const LAZY_THRESHOLD = 10;
// Les anciens rapports utilisent des emojis dans les titres.
const DETAILS_HEADINGS = ['## Analyses Détaillées', '## 📄 Analyses Détaillées'];
const ERRORS_HEADINGS = ['\n## Erreurs', '\n## ⚠️ Erreurs'];

const findHeading = (text, headings, from = 0) => {
  for (const heading of headings) {
    const index = text.indexOf(heading, from);
    if (index !== -1) return { index, length: heading.length };
  }
  return null;
};

const markdownComponents = {
  h1: ({ node, ...props }) => <Typography variant="h4" gutterBottom {...props} />,
  h2: ({ node, ...props }) => <Typography variant="h5" gutterBottom {...props} />,
  p: ({ node, ...props }) => <Typography variant="body1" paragraph {...props} />,
  li: ({ node, ...props }) => <Typography component="li" variant="body1" {...props} />,
};

const ReportMarkdown = ({ children }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
    {children}
  </ReactMarkdown>
);

// Decoupe le rapport : synthese, analyses detaillees (une entree par CV), erreurs.
const splitReport = (report) => {
  const details = findHeading(report, DETAILS_HEADINGS);
  if (!details) return { head: report, items: [], tail: '' };
  const afterHeading = details.index + details.length;
  const errors = findHeading(report, ERRORS_HEADINGS, afterHeading);
  const errorsStart = errors ? errors.index : -1;
  const detailsEnd = errorsStart === -1 ? report.length : errorsStart;
  const items = report
    .slice(afterHeading, detailsEnd)
    .split(/(?=^### )/m)
    .map((chunk) => chunk.replace(/\n---\s*$/, '').trim())
    .filter(Boolean)
    .map((chunk, index) => ({
      key: index,
      title: chunk.split('\n', 1)[0].replace(/^###\s*/, ''),
      body: chunk.split('\n').slice(1).join('\n'),
    }));
  if (items.length <= LAZY_THRESHOLD) return { head: report, items: [], tail: '' };
  return {
    head: report.slice(0, afterHeading),
    items,
    tail: errorsStart === -1 ? '' : report.slice(errorsStart),
  };
};

const AnalysisReport = ({ report, onExportPDF, onExportFile }) => {
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const sections = useMemo(() => splitReport(report || ''), [report]);
  useEffect(() => setVisibleCount(PAGE_SIZE), [report]);
  if (!report) return null;

  return (
    <Box sx={{ position: 'relative' }}>
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 2
        }}
      >
        <Tooltip title="Exporter">
          <IconButton
            onClick={(e) => (onExportFile ? setMenuAnchor(e.currentTarget) : onExportPDF())}
            color="primary"
            size="large"
          >
            <FileDownloadIcon />
          </IconButton>
        </Tooltip>
        <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={() => setMenuAnchor(null)}>
          {[
            ['html', 'Rapport HTML (interactif)'],
            ['xlsx', 'Classement Excel'],
            ['pdf', 'PDF résumé (classement + top 10)'],
          ].map(([format, label]) => (
            <MenuItem
              key={format}
              onClick={() => {
                setMenuAnchor(null);
                onExportFile(format);
              }}
            >
              {label}
            </MenuItem>
          ))}
        </Menu>
      </Box>

      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3, pr: 8 }}>
        📋 Rapport d'Analyse
      </Typography>

      <Box
        className="report-content"
        sx={{
          '& table': {
            borderCollapse: 'collapse',
            width: '100%',
            mb: 2,
          },
          '& th, & td': {
            border: '1px solid rgba(224, 224, 224, 1)',
            padding: '8px 16px',
            textAlign: 'left',
          },
          '& th': {
            backgroundColor: 'primary.main',
            color: 'white',
          },
          '& tr:nth-of-type(even)': {
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          },
          '& tr:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
          '& h1': {
            color: 'primary.main',
            fontSize: '1.5rem',
            fontWeight: 600,
            mb: 2,
          },
          '& h2': {
            color: 'primary.dark',
            fontSize: '1.25rem',
            fontWeight: 500,
            mb: 2,
            mt: 3,
          },
          '& p': {
            mb: 2,
            lineHeight: 1.6,
          },
          '& ul, & ol': {
            pl: 3,
            mb: 2,
          },
          '& li': {
            mb: 1,
          },
          '& code': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
            padding: '2px 4px',
            borderRadius: 1,
            fontFamily: 'monospace',
          },
          '& blockquote': {
            borderLeft: '4px solid',
            borderColor: 'primary.main',
            pl: 2,
            py: 1,
            my: 2,
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          }
        }}
      >
        {sections.head && <ReportMarkdown>{sections.head}</ReportMarkdown>}
        {sections.items.slice(0, visibleCount).map((item) => (
          <Accordion key={item.key} disableGutters TransitionProps={{ unmountOnExit: true }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">{item.title}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <ReportMarkdown>{item.body}</ReportMarkdown>
            </AccordionDetails>
          </Accordion>
        ))}
        {sections.items.length > visibleCount && (
          <Box sx={{ textAlign: 'center', my: 2 }}>
            <Button onClick={() => setVisibleCount((n) => n + PAGE_SIZE)}>
              Afficher plus ({sections.items.length - visibleCount} restants)
            </Button>
          </Box>
        )}
        {sections.tail && <ReportMarkdown>{sections.tail}</ReportMarkdown>}
      </Box>
    </Box>
  );
};

export default AnalysisReport;
