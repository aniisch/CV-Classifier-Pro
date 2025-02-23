import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';

const ExportButton = ({ onClick, disabled }) => {
  return (
    <span>
      <Tooltip title="Exporter en PDF">
        <span>
          <IconButton
            onClick={onClick}
            disabled={disabled}
            color="primary"
            size="small"
          >
            <PictureAsPdfIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
    </span>
  );
};

export default ExportButton;
