import React from 'react';
import {Composition} from 'remotion';
import {Video, TOTAL} from './Main';

export const Root: React.FC = () => (
  <>
    <Composition id="Landscape" component={Video} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
    <Composition id="Vertical" component={Video} durationInFrames={TOTAL} fps={30} width={1080} height={1920} />
  </>
);
