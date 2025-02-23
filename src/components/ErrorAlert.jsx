import React from 'react';
import { 
  Alert, 
  AlertTitle, 
  Collapse, 
  IconButton,
  Box
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const ErrorAlert = ({ error, onClose, severity = 'error' }) => {
  if (!error) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Collapse in={!!error}>
        <Alert
          severity={severity}
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={onClose}
            >
              <CloseIcon fontSize="inherit" />
            </IconButton>
          }
          sx={{
            '& .MuiAlert-message': {
              width: '100%'
            }
          }}
        >
          <AlertTitle>
            {severity === 'error' ? 'Erreur' : 'Attention'}
          </AlertTitle>
          {error.message}
          {error.details && Object.keys(error.details).length > 0 && (
            <Box 
              component="pre"
              sx={{
                mt: 1,
                p: 1,
                bgcolor: 'rgba(0, 0, 0, 0.04)',
                borderRadius: 1,
                fontSize: '0.875rem',
                overflow: 'auto'
              }}
            >
              {JSON.stringify(error.details, null, 2)}
            </Box>
          )}
        </Alert>
      </Collapse>
    </Box>
  );
};

export default ErrorAlert;
